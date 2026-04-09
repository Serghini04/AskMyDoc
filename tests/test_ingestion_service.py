from types import SimpleNamespace

from app.repositories.document_repo import DocumentRepository
from app.models.document import Chunk, Document
from app.services import ingestion


class DummyEmbeddingService:
    def embed_text(self, text: str) -> list[float]:
        return [float(len(text)), 1.0, 2.0]


def test_process_document_persists_chunks_and_upserts(db_session, monkeypatch):
    doc = DocumentRepository.create(
        db=db_session,
        filename="doc.txt",
        file_hash="f" * 64,
    )

    monkeypatch.setattr(ingestion, "extract_text", lambda *_: "raw")
    monkeypatch.setattr(ingestion, "clean_text", lambda text: text)
    monkeypatch.setattr(
        ingestion,
        "chunk_document_text",
        lambda *_args, **_kwargs: ["chunk-0", "chunk-1", "chunk-2"],
    )

    captured = {"points": None}

    class FakeQdrant:
        def upsert_points(self, points):
            captured["points"] = points

    monkeypatch.setattr(ingestion, "get_qdrant_service", lambda: FakeQdrant())

    count = ingestion.process_document(
        db=db_session,
        doc_id=doc.id,
        file_path="unused.txt",
        ext=".txt",
        embedding_service=DummyEmbeddingService(),
    )

    assert count == 3

    chunks = (
        db_session.query(Chunk)
        .filter(Chunk.document_id == doc.id)
        .order_by(Chunk.chunk_index.asc())
        .all()
    )
    assert [chunk.chunk_index for chunk in chunks] == [0, 1, 2]
    assert [chunk.content for chunk in chunks] == ["chunk-0", "chunk-1", "chunk-2"]

    assert captured["points"] is not None
    assert [point["payload"]["chunk_index"] for point in captured["points"]] == [0, 1, 2]
    assert all(point["payload"]["document_id"] == str(doc.id) for point in captured["points"])


def test_process_document_background_updates_status_success_and_failure(
    session_maker, monkeypatch
):
    monkeypatch.setattr(ingestion, "SessionLocal", session_maker)

    success_db = session_maker()
    success_doc = DocumentRepository.create(
        db=success_db,
        filename="ok.txt",
        file_hash="a" * 64,
    )
    success_db.close()

    monkeypatch.setattr(ingestion, "process_document", lambda *_args, **_kwargs: 2)

    ingestion.process_document_background(
        doc_id=success_doc.id,
        file_path="unused.txt",
        ext=".txt",
        embedding_service=SimpleNamespace(embed_text=lambda _text: [0.0]),
    )

    check_success = session_maker()
    updated_success = check_success.query(Document).filter(Document.id == success_doc.id).first()
    assert updated_success is not None
    assert updated_success.status == "COMPLETED"
    check_success.close()

    failure_db = session_maker()
    failure_doc = DocumentRepository.create(
        db=failure_db,
        filename="bad.txt",
        file_hash="b" * 64,
    )
    failure_db.close()

    def fail_process(*_args, **_kwargs):
        raise RuntimeError("boom")

    monkeypatch.setattr(ingestion, "process_document", fail_process)

    ingestion.process_document_background(
        doc_id=failure_doc.id,
        file_path="unused.txt",
        ext=".txt",
        embedding_service=SimpleNamespace(embed_text=lambda _text: [0.0]),
    )

    check_failure = session_maker()
    updated_failure = check_failure.query(Document).filter(Document.id == failure_doc.id).first()
    assert updated_failure is not None
    assert updated_failure.status == "FAILED"
    check_failure.close()
