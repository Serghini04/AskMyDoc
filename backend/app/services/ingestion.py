from __future__ import annotations

import os
import re
import logging
from uuid import UUID

import fitz  # PyMuPDF
from langchain_text_splitters import RecursiveCharacterTextSplitter
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models.document import Chunk, Document
from app.repositories.chunk_repo import ChunkRepository
from app.repositories.document_repo import DocumentRepository
from app.services.embeddings import BaseEmbeddingService, get_embedding_service
from app.services.qdrant import get_qdrant_service


UPLOAD_DIR = "uploads"
IN_PROGRESS_STATUSES = ("PENDING", "PROCESSING")


def stored_file_path(doc_id: UUID | str, filename: str) -> str:
    """Where an upload lives on disk: uploads/<doc_id><ext>."""
    _, ext = os.path.splitext(filename)
    return os.path.join(UPLOAD_DIR, f"{doc_id}{ext.lower()}")


def extract_text(file_path: str, ext: str) -> str:
    raw_text = ""
    if ext == ".pdf":
        doc = fitz.open(file_path)
        for page_num in range(len(doc)):
            raw_text += doc.load_page(page_num).get_text()
        doc.close()
    elif ext == ".txt":
        with open(file_path, "r", encoding="utf-8") as f:
            raw_text = f.read()
    else:
        raise ValueError(f"Unsupported extension for extraction: {ext}")
    return raw_text


def clean_text(text: str) -> str:
    text = re.sub(r"(\w+)-\n(\w+)", r"\1\2", text)
    text = re.sub(r"\n+", " ", text)
    text = re.sub(r"\s{2,}", " ", text)
    return text.strip()


def chunk_document_text(text: str, chunk_size: int = 1000, chunk_overlap: int = 200) -> list[str]:
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        length_function=len,
        separators=["\n\n", "\n", " ", ""],
    )
    return splitter.split_text(text)


def process_document(
    db: Session,
    doc_id: UUID | str,
    file_path: str,
    ext: str,
    embedding_service: BaseEmbeddingService,
) -> int:
    doc = db.query(Document).filter(Document.id == doc_id).first()
    if not doc:
        raise ValueError(f"Document {doc_id} not found in database.")

    raw_text = extract_text(file_path, ext)
    clean_str = clean_text(raw_text)
    chunks = chunk_document_text(clean_str, chunk_size=1000, chunk_overlap=200)

    # Idempotent: a retry (e.g. after a crash mid-ingestion) replaces any
    # partial output instead of duplicating it.
    get_qdrant_service().delete_points_by_document(str(doc_id))
    db.query(Chunk).filter(Chunk.document_id == doc_id).delete(synchronize_session=False)
    db.commit()

    saved_chunks = ChunkRepository.create_bulk(db=db, document_id=doc_id, chunks_data=chunks)

    qdrant_payloads = []
    for chunk in saved_chunks:
        vector = embedding_service.embed_text(chunk.content)
        qdrant_payloads.append({
            "id": str(chunk.id),
            "vector": vector,
            "payload": {
                "document_id": str(doc_id),
                "session_id": str(doc.session_id),
                "chunk_index": chunk.chunk_index,
            },
        })

    get_qdrant_service().upsert_points(qdrant_payloads)
    return len(chunks)


def process_document_background(
    doc_id: UUID | str,
    file_path: str,
    ext: str,
    embedding_service: BaseEmbeddingService | None = None,
):
    """Wrapper for FastAPI BackgroundTasks — owns its own DB session."""
    with SessionLocal() as db:
        try:
            if embedding_service is None:
                embedding_service = get_embedding_service()

            logging.info("Starting background processing for document %s", doc_id)
            DocumentRepository.update_status(db, doc_id, "PROCESSING")
            chunks_created = process_document(db, doc_id, file_path, ext, embedding_service)
            DocumentRepository.update_status(db, doc_id, "COMPLETED")
            logging.info("Processed %d chunks for document %s", chunks_created, doc_id)
        except Exception as e:
            logging.error("Failed to process document %s: %s", doc_id, e)
            DocumentRepository.update_status(db, doc_id, "FAILED")


def resume_unfinished_documents() -> None:
    """
    Re-run ingestion for documents left PENDING/PROCESSING by a previous process.

    BackgroundTasks live in the API process, so a restart or deploy mid-upload
    kills the job and would leave the document stuck forever. Called once at
    startup; safe because process_document is idempotent.
    """
    with SessionLocal() as db:
        stuck = (
            db.query(Document.id, Document.filename)
            .filter(Document.status.in_(IN_PROGRESS_STATUSES))
            .all()
        )

    if not stuck:
        return
    logging.info("Resuming %d unfinished document(s).", len(stuck))

    for doc_id, filename in stuck:
        file_path = stored_file_path(doc_id, filename)
        if not os.path.exists(file_path):
            logging.error("Cannot resume document %s: file %s is missing.", doc_id, file_path)
            with SessionLocal() as db:
                DocumentRepository.update_status(db, doc_id, "FAILED")
            continue
        _, ext = os.path.splitext(filename)
        process_document_background(doc_id, file_path, ext.lower())
