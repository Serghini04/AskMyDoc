

from typing import Generator
from app.database import SessionLocal
from sqlalchemy.orm import Session


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
    return request.app.state.embeding_service