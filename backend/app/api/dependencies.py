from typing import Generator

from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.services.embeddings import BaseEmbeddingService
from app.services.embeddings import get_embedding_service as _get_embedding_service


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_embedding_service() -> BaseEmbeddingService:
    return _get_embedding_service()
