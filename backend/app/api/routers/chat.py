from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Query, status

from app.api.dependencies import ChatServiceDep
from app.schemas.chat import (
    ChatMessageResponse,
    ChatRequest,
    ChatSessionResponse,
    ChatSessionUpdate,
)

router = APIRouter(prefix="/sessions", tags=["Chat Sessions"])


@router.post("/", response_model=ChatSessionResponse, status_code=status.HTTP_201_CREATED)
def create_session(service: ChatServiceDep):
    return service.create_session()


@router.get("/", response_model=list[ChatSessionResponse])
def list_sessions(
    service: ChatServiceDep,
    skip: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
):
    """Sessions for the sidebar, newest first."""
    return service.list_sessions(offset=skip, limit=limit)


@router.get("/{session_id}", response_model=ChatSessionResponse)
def get_session(session_id: UUID, service: ChatServiceDep):
    """A session with its messages and documents."""
    return service.get_session(session_id)


@router.patch("/{session_id}", response_model=ChatSessionResponse)
def rename_session(session_id: UUID, payload: ChatSessionUpdate, service: ChatServiceDep):
    return service.rename_session(session_id, payload.title)


@router.delete("/{session_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_session(session_id: UUID, service: ChatServiceDep) -> None:
    """Delete a session with its messages, documents, chunks, vectors, and files."""
    service.delete_session(session_id)


@router.post("/{session_id}/chat", response_model=ChatMessageResponse)
def ask(session_id: UUID, request: ChatRequest, service: ChatServiceDep):
    """The RAG endpoint: answer a question from the session's documents."""
    return service.ask(session_id, request.message)
