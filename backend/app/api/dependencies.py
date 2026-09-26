from collections.abc import Iterator
from typing import Annotated

from fastapi import Depends
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.services import embeddings as embeddings_module
from app.services.chat_service import ChatService
from app.services.document_service import DocumentService
from app.services.embeddings import BaseEmbeddingService
from app.services.llm import BaseLLMService, get_llm_service


def get_db() -> Iterator[Session]:
    with SessionLocal() as db:
        yield db


def get_embedding_service() -> BaseEmbeddingService:
    return embeddings_module.get_embedding_service()


DbSession = Annotated[Session, Depends(get_db)]


def get_chat_service(
    db: DbSession,
    llm: Annotated[BaseLLMService, Depends(get_llm_service)],
    embeddings: Annotated[BaseEmbeddingService, Depends(get_embedding_service)],
) -> ChatService:
    return ChatService(db, llm, embeddings)


def get_document_service(db: DbSession) -> DocumentService:
    return DocumentService(db)


ChatServiceDep = Annotated[ChatService, Depends(get_chat_service)]
DocumentServiceDep = Annotated[DocumentService, Depends(get_document_service)]
