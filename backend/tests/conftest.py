"""
Shared fixtures. Tests run against SQLite and in-memory fakes for every
external service (embeddings, LLM, Qdrant), so they need no network and no keys.
"""

from collections.abc import Iterator, Sequence
from uuid import UUID

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

import app.models  # noqa: F401  (registers every table on Base.metadata)
from app.api.dependencies import get_db, get_embedding_service
from app.config import settings
from app.database import Base
from app.main import create_app
from app.services import ingestion, qdrant
from app.services.embeddings import BaseEmbeddingService, Vector
from app.services.llm import BaseLLMService, ChatTurn, get_llm_service


class DummyEmbeddingService(BaseEmbeddingService):
    def embed_texts(self, texts: Sequence[str]) -> list[Vector]:
        return [[float(len(text)), 1.0, 2.0] for text in texts]


class DummyLLMService(BaseLLMService):
    def __init__(self) -> None:
        self.contexts: list[str] = []

    def generate_answer(self, context: str, history: Sequence[ChatTurn], question: str) -> str:
        self.contexts.append(context)
        return "test-answer"

    def generate_title(self, question: str, answer: str) -> str:
        return "Generated Title"


class FakeQdrantService:
    """In-memory stand-in for QdrantService with the same public interface."""

    def __init__(self) -> None:
        self.points: dict[UUID, qdrant.ChunkPoint] = {}
        self.deleted_documents: list[UUID] = []

    def upsert_chunks(self, points: Sequence[qdrant.ChunkPoint]) -> None:
        self.points.update({point.chunk_id: point for point in points})

    def search_chunk_ids(self, query_vector: Vector, session_id: UUID, limit: int) -> list[UUID]:
        hits = [p.chunk_id for p in self.points.values() if p.session_id == session_id]
        return hits[:limit]

    def delete_document(self, document_id: UUID) -> None:
        self.deleted_documents.append(document_id)
        self.points = {k: p for k, p in self.points.items() if p.document_id != document_id}


@pytest.fixture(autouse=True)
def upload_dir(tmp_path, monkeypatch):
    """Every test gets its own upload folder — never the real uploads/."""
    path = tmp_path / "uploads"
    monkeypatch.setattr(settings, "UPLOAD_DIR", str(path))
    return path


@pytest.fixture
def fake_qdrant(monkeypatch) -> FakeQdrantService:
    fake = FakeQdrantService()
    monkeypatch.setattr(qdrant, "get_qdrant_service", lambda: fake)
    return fake


@pytest.fixture
def db_engine(tmp_path):
    engine = create_engine(
        f"sqlite:///{tmp_path / 'test.db'}", connect_args={"check_same_thread": False}
    )
    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)
    engine.dispose()


@pytest.fixture
def session_maker(db_engine) -> sessionmaker[Session]:
    return sessionmaker(bind=db_engine, autoflush=False)


@pytest.fixture
def db_session(session_maker) -> Iterator[Session]:
    with session_maker() as session:
        yield session


@pytest.fixture
def llm() -> DummyLLMService:
    return DummyLLMService()


@pytest.fixture
def ingest_calls(monkeypatch) -> list[UUID]:
    """Record scheduled ingestions instead of running them (TestClient runs
    background tasks inline). Tests that want real ingestion call it themselves."""
    calls: list[UUID] = []
    monkeypatch.setattr(ingestion, "ingest_document", lambda document_id: calls.append(document_id))
    return calls


@pytest.fixture
def api_client(session_maker, fake_qdrant, llm, ingest_calls) -> Iterator[TestClient]:
    app = create_app(resume_ingestion=False)

    def override_get_db() -> Iterator[Session]:
        with session_maker() as db:
            yield db

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_embedding_service] = DummyEmbeddingService
    app.dependency_overrides[get_llm_service] = lambda: llm

    with TestClient(app) as client:
        yield client
