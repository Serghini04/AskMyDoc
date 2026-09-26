from collections.abc import Generator

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.api.dependencies import get_db, get_embedding_service
from app.api.routers import documents, chat
from app.services import ingestion
from app.database import Base
from app.services.llm import get_llm_service
from app.models import chat as chat_models  # noqa: F401
from app.models import document as document_models  # noqa: F401


class DummyEmbeddingService:
    def embed_text(self, text: str) -> list[float]:
        return [float(len(text)), 1.0, 2.0]


class FakeQdrantService:
    def __init__(self):
        self.deleted_documents: list[str] = []

    def delete_points_by_document(self, document_id: str) -> None:
        self.deleted_documents.append(document_id)


class DummyLLMService:
    def generate_answer(self, system_prompt: str, context: str, history, question: str) -> str:
        return "test-answer"

    def generate_title(self, question: str, answer: str) -> str:
        return "Generated Title"


@pytest.fixture
def db_engine(tmp_path):
    db_path = tmp_path / "test.db"
    engine = create_engine(
        f"sqlite:///{db_path}", connect_args={"check_same_thread": False}
    )
    Base.metadata.create_all(bind=engine)
    try:
        yield engine
    finally:
        Base.metadata.drop_all(bind=engine)


@pytest.fixture
def session_maker(db_engine):
    return sessionmaker(autocommit=False, autoflush=False, bind=db_engine)


@pytest.fixture
def db_session(session_maker) -> Generator[Session, None, None]:
    session = session_maker()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def fake_qdrant() -> FakeQdrantService:
    return FakeQdrantService()


@pytest.fixture
def api_client(
    tmp_path, session_maker, monkeypatch, fake_qdrant
) -> Generator[TestClient, None, None]:
    upload_dir = tmp_path / "uploads"
    upload_dir.mkdir(parents=True, exist_ok=True)
    # stored_file_path() reads ingestion.UPLOAD_DIR; patch it so tests never
    # write into the real uploads/ folder.
    monkeypatch.setattr(ingestion, "UPLOAD_DIR", str(upload_dir))
    monkeypatch.setattr(ingestion, "get_qdrant_service", lambda: fake_qdrant)

    app = FastAPI()
    app.include_router(documents.router, prefix="/api/v1")
    app.include_router(chat.router, prefix="/api/v1")

    def override_get_db() -> Generator[Session, None, None]:
        db = session_maker()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_embedding_service] = lambda: DummyEmbeddingService()
    app.dependency_overrides[get_llm_service] = lambda: DummyLLMService()

    with TestClient(app) as client:
        yield client

    app.dependency_overrides.clear()
