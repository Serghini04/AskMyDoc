from collections.abc import Generator

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.api.dependencies import get_db
from app.api.routers import documents
from app.models.document import Base


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
def api_client(tmp_path, session_maker, monkeypatch) -> Generator[TestClient, None, None]:
    upload_dir = tmp_path / "uploads"
    upload_dir.mkdir(parents=True, exist_ok=True)
    monkeypatch.setattr(documents, "UPLOAD_DIR", str(upload_dir))

    app = FastAPI()
    app.include_router(documents.router, prefix="/api/v1")

    def override_get_db() -> Generator[Session, None, None]:
        db = session_maker()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as client:
        yield client

    app.dependency_overrides.clear()
