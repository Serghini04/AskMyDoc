from uuid import UUID

import pymupdf
import pytest
from sqlalchemy import select

from app.models import ChatSession, Chunk, Document, DocumentStatus
from app.services import ingestion, storage
from app.services.embeddings import BaseEmbeddingService, EmbeddingUnavailableError
from tests.conftest import DummyEmbeddingService


class DownEmbeddings(BaseEmbeddingService):
    def embed_texts(self, texts):
        raise EmbeddingUnavailableError("provider down")


def _document(db, filename="doc.txt", content="hello world", status=DocumentStatus.PENDING):
    chat_session = ChatSession(title="ingestion test")
    db.add(chat_session)
    db.flush()
    document = Document(
        filename=filename,
        file_hash=filename.ljust(64, "0")[:64],
        file_size_bytes=len(content or ""),
        session_id=chat_session.id,
        status=status,
    )
    db.add(document)
    db.commit()
    if content is not None:
        storage.stored_file_path(document.id, filename).write_text(content, encoding="utf-8")
    return document


def _chunks(db, document_id: UUID) -> list[Chunk]:
    stmt = select(Chunk).where(Chunk.document_id == document_id).order_by(Chunk.chunk_index)
    return list(db.scalars(stmt))


# --- text processing ---------------------------------------------------------


def test_extract_text_from_txt_and_pdf(tmp_path):
    txt = tmp_path / "a.txt"
    txt.write_text("plain text", encoding="utf-8")
    assert ingestion.extract_text(txt) == "plain text"

    pdf_path = tmp_path / "a.pdf"
    with pymupdf.open() as pdf:
        pdf.new_page().insert_text((72, 72), "Hello from a PDF")
        pdf.save(pdf_path)
    assert "Hello from a PDF" in ingestion.extract_text(pdf_path)


def test_extract_text_rejects_other_types(tmp_path):
    with pytest.raises(ValueError):
        ingestion.extract_text(tmp_path / "a.docx")


def test_clean_text_joins_hyphenation_and_collapses_whitespace():
    assert ingestion.clean_text("docu-\nment\n\nline   two ") == "document line two"


# --- index_document ----------------------------------------------------------


def test_index_document_persists_chunks_and_vectors(db_session, fake_qdrant, monkeypatch):
    document = _document(db_session)
    monkeypatch.setattr(ingestion, "split_into_chunks", lambda _text: ["c-0", "c-1", "c-2"])

    count = ingestion.index_document(db_session, document, DummyEmbeddingService())
    db_session.commit()

    assert count == 3
    chunks = _chunks(db_session, document.id)
    assert [c.content for c in chunks] == ["c-0", "c-1", "c-2"]
    # Each vector's point ID is its chunk's ID, tagged with document and session.
    assert set(fake_qdrant.points) == {c.id for c in chunks}
    point = fake_qdrant.points[chunks[1].id]
    assert (point.document_id, point.session_id, point.chunk_index) == (
        document.id,
        document.session_id,
        1,
    )


def test_index_document_is_idempotent(db_session, fake_qdrant, monkeypatch):
    document = _document(db_session)
    monkeypatch.setattr(ingestion, "split_into_chunks", lambda _text: ["a", "b"])

    for _ in range(2):
        ingestion.index_document(db_session, document, DummyEmbeddingService())
        db_session.commit()

    assert len(_chunks(db_session, document.id)) == 2
    assert len(fake_qdrant.points) == 2


def test_index_document_writes_nothing_when_embedding_fails(db_session, fake_qdrant):
    document = _document(db_session)

    with pytest.raises(EmbeddingUnavailableError):
        ingestion.index_document(db_session, document, DownEmbeddings())

    # Embedding runs before any write, so a provider outage leaves no partial state.
    assert fake_qdrant.deleted_documents == []
    assert fake_qdrant.points == {}
    assert _chunks(db_session, document.id) == []


# --- ingest_document (background entry point) ---------------------------------


def test_ingest_document_marks_completed(session_maker, db_session, fake_qdrant, monkeypatch):
    monkeypatch.setattr(ingestion, "SessionLocal", session_maker)
    document = _document(db_session)

    ingestion.ingest_document(document.id, embeddings=DummyEmbeddingService())

    db_session.expire_all()
    assert db_session.get(Document, document.id).status == DocumentStatus.COMPLETED


def test_ingest_document_marks_failed_on_error(session_maker, db_session, fake_qdrant, monkeypatch):
    monkeypatch.setattr(ingestion, "SessionLocal", session_maker)
    document = _document(db_session)

    ingestion.ingest_document(document.id, embeddings=DownEmbeddings())

    db_session.expire_all()
    assert db_session.get(Document, document.id).status == DocumentStatus.FAILED


def test_ingest_document_ignores_deleted_document(session_maker, monkeypatch):
    monkeypatch.setattr(ingestion, "SessionLocal", session_maker)
    ingestion.ingest_document(UUID(int=0), embeddings=DummyEmbeddingService())  # no error


# --- recovery & cleanup ------------------------------------------------------


def test_resume_unfinished_documents(session_maker, db_session, monkeypatch):
    monkeypatch.setattr(ingestion, "SessionLocal", session_maker)
    stuck = _document(db_session, "stuck.txt", status=DocumentStatus.PROCESSING)
    missing = _document(db_session, "missing.txt", content=None, status=DocumentStatus.PENDING)
    done = _document(db_session, "done.txt", status=DocumentStatus.COMPLETED)

    resumed: list[UUID] = []
    monkeypatch.setattr(ingestion, "ingest_document", resumed.append)

    ingestion.resume_unfinished_documents()

    assert resumed == [stuck.id]
    db_session.expire_all()
    assert db_session.get(Document, missing.id).status == DocumentStatus.FAILED
    assert db_session.get(Document, done.id).status == DocumentStatus.COMPLETED


def test_purge_document_artifacts_removes_file_and_vectors(db_session, fake_qdrant):
    document = _document(db_session)
    path = storage.stored_file_path(document.id, document.filename)

    ingestion.purge_document_artifacts(document.id, document.filename)

    assert not path.exists()
    assert fake_qdrant.deleted_documents == [document.id]
