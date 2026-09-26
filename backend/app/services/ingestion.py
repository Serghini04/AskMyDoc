"""
Document ingestion: extract -> clean -> chunk -> embed -> store (Postgres + Qdrant).

Runs outside the request (FastAPI BackgroundTasks), so every entry point here
owns its own DB session. Indexing is idempotent, which makes startup recovery
and `make reindex` safe to run at any time.
"""

import logging
import re
from pathlib import Path
from uuid import UUID

import pymupdf
from langchain_text_splitters import RecursiveCharacterTextSplitter
from sqlalchemy.orm import Session

from app.config import settings
from app.database import SessionLocal
from app.models.document import Document
from app.models.enums import IN_PROGRESS_STATUSES, DocumentStatus
from app.repositories.chunk_repo import ChunkRepository
from app.repositories.document_repo import DocumentRepository
from app.services import qdrant, storage
from app.services.embeddings import BaseEmbeddingService, get_embedding_service

logger = logging.getLogger(__name__)


# --- text processing ---------------------------------------------------------


def extract_text(path: Path) -> str:
    extension = path.suffix.lower()
    if extension == ".pdf":
        with pymupdf.open(path) as pdf:
            return "".join(page.get_text() for page in pdf)
    if extension == ".txt":
        return path.read_text(encoding="utf-8")
    raise ValueError(f"Unsupported extension for extraction: {extension}")


def clean_text(text: str) -> str:
    text = re.sub(r"(\w+)-\n(\w+)", r"\1\2", text)  # re-join hyphenated line breaks
    text = re.sub(r"\n+", " ", text)
    text = re.sub(r"\s{2,}", " ", text)
    return text.strip()


def split_into_chunks(text: str) -> list[str]:
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=settings.CHUNK_SIZE_CHARS,
        chunk_overlap=settings.CHUNK_OVERLAP_CHARS,
        length_function=len,
        separators=["\n\n", "\n", " ", ""],
    )
    return splitter.split_text(text)


# --- indexing ----------------------------------------------------------------


def index_document(db: Session, document: Document, embeddings: BaseEmbeddingService) -> int:
    """
    (Re)build a document's chunks and vectors. Idempotent: previous output is
    replaced, never duplicated. Leaves the transaction for the caller to commit.
    Returns the number of chunks.
    """
    path = storage.stored_file_path(document.id, document.filename)
    texts = split_into_chunks(clean_text(extract_text(path)))

    # Embed first: it's the slow, network-bound step, so if the provider
    # fails nothing has been written yet.
    vectors = embeddings.embed_texts(texts)

    vector_store = qdrant.get_qdrant_service()
    vector_store.delete_document(document.id)
    chunks_repo = ChunkRepository(db)
    chunks_repo.delete_for_document(document.id)
    chunks = chunks_repo.add_all(document.id, texts)

    vector_store.upsert_chunks(
        [
            qdrant.ChunkPoint(
                chunk_id=chunk.id,
                document_id=document.id,
                session_id=document.session_id,
                chunk_index=chunk.chunk_index,
                vector=vector,
            )
            for chunk, vector in zip(chunks, vectors, strict=True)
        ]
    )
    return len(chunks)


def ingest_document(document_id: UUID, embeddings: BaseEmbeddingService | None = None) -> None:
    """Background-task entry point: index one document and record the outcome."""
    with SessionLocal() as db:
        documents = DocumentRepository(db)
        document = documents.get(document_id)
        if document is None:
            logger.warning("Document %s was deleted before ingestion started", document_id)
            return

        document.status = DocumentStatus.PROCESSING
        db.commit()
        logger.info("Ingesting document %s", document_id)

        try:
            chunk_count = index_document(db, document, embeddings or get_embedding_service())
            document.status = DocumentStatus.COMPLETED
            db.commit()
            logger.info("Indexed %d chunks for document %s", chunk_count, document_id)
        except Exception:
            logger.exception("Failed to ingest document %s", document_id)
            db.rollback()
            document.status = DocumentStatus.FAILED
            db.commit()


def resume_unfinished_documents() -> None:
    """
    Re-run ingestion for documents left PENDING/PROCESSING by a previous process.

    BackgroundTasks live in the API process, so a restart mid-upload kills the
    job and would leave the document stuck forever. Called once at startup.
    """
    with SessionLocal() as db:
        to_resume: list[UUID] = []
        for document in DocumentRepository(db).list_with_status(IN_PROGRESS_STATUSES):
            if storage.stored_file_path(document.id, document.filename).exists():
                to_resume.append(document.id)
            else:
                logger.error("Cannot resume document %s: its file is missing", document.id)
                document.status = DocumentStatus.FAILED
        db.commit()

    if to_resume:
        logger.info("Resuming %d unfinished document(s)", len(to_resume))
    for document_id in to_resume:
        ingest_document(document_id)


def purge_document_artifacts(document_id: UUID, filename: str) -> None:
    """
    Best-effort removal of a document's file and vectors. Call after the DB
    delete has committed: leftovers are harmless (retrieval only returns chunks
    that still exist in Postgres), whereas the reverse order could leave a row
    pointing at a file that's already gone.
    """
    storage.discard(storage.stored_file_path(document_id, filename))
    try:
        qdrant.get_qdrant_service().delete_document(document_id)
    except Exception:
        logger.warning("Failed to delete vectors for document %s", document_id, exc_info=True)
