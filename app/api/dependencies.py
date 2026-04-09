

from typing import Generator
from fastapi import Request
from app.database import SessionLocal
from sqlalchemy.orm import Session
from app.services.embeddings import BaseEmbeddingService, BGEM3EmbeddingService


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
        
        
def get_embedding_service(request: Request) -> BaseEmbeddingService:
    """
    Retrieves the singleton embedding service from the global app state.
    """
    if request.app.state.embedding_service is None:
        request.app.state.embedding_service = BGEM3EmbeddingService()

    return request.app.state.embedding_service