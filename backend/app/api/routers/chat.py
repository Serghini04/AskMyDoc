import logging
from uuid import UUID
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.dependencies import get_db, get_embedding_service
from app.services.embeddings import BaseEmbeddingService
from app.schemas.chat import ChatSessionResponse, ChatRequest, ChatMessageResponse, ChatSessionUpdate
from app.repositories.chat_repo import ChatSessionRepository, ChatMessageRepository
from app.services.retrieval import RetrievalService
from app.services.llm import BaseLLMService, LLMUnavailableError, get_llm_service
from app.services.qdrant import get_qdrant_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/sessions", tags=["Chat Sessions"])

DEFAULT_SESSION_TITLE = "New Chat"
MAX_TITLE_LENGTH = 255


def _clean_title(raw: str) -> str:
    """Normalize an LLM-generated title: first line, unquoted, length-capped."""
    if not raw:
        return ""
    title = raw.strip().splitlines()[0].strip().strip('"“”\'')
    return title[:MAX_TITLE_LENGTH].strip()


def _fallback_title(question: str) -> str:
    """Derive a title from the question when the LLM is unavailable."""
    words = question.strip().split()
    return " ".join(words[:6])[:MAX_TITLE_LENGTH].strip() or DEFAULT_SESSION_TITLE

@router.post("/", response_model=ChatSessionResponse, status_code=status.HTTP_201_CREATED)
async def create_chat_session(db: Session = Depends(get_db)):
    """Creates a brand new, empty chat session (Clicking 'New Chat')."""
    return ChatSessionRepository.create(db=db)

@router.get("/", response_model=List[ChatSessionResponse])
async def list_chat_sessions(skip: int = 0, limit: int = 50, db: Session = Depends(get_db)):
    """Fetches all chat sessions for the sidebar history."""
    return ChatSessionRepository.get_all(db=db, skip=skip, limit=limit)

@router.get("/{session_id}", response_model=ChatSessionResponse)
async def get_chat_session(session_id: UUID, db: Session = Depends(get_db)):
    """Loads a specific chat session, including all its messages and documents."""
    session = ChatSessionRepository.get_by_id(db=db, session_id=session_id)
    if not session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")
    return session


@router.patch("/{session_id}", response_model=ChatSessionResponse)
async def rename_chat_session(
    session_id: UUID,
    payload: ChatSessionUpdate,
    db: Session = Depends(get_db),
):
    """Rename a chat session (e.g. editing its title in the sidebar)."""
    session = ChatSessionRepository.get_by_id(db=db, session_id=session_id)
    if not session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")
    return ChatSessionRepository.update_title(db=db, session=session, title=payload.title)


@router.delete("/{session_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_chat_session(session_id: UUID, db: Session = Depends(get_db)):
    """Delete a session and all its messages, documents, chunks, and vectors."""
    session = ChatSessionRepository.get_by_id(db=db, session_id=session_id)
    if not session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")

    for doc in session.documents:
        try:
            get_qdrant_service().delete_points_by_document(str(doc.id))
        except Exception as exc:
            logger.warning("Failed to delete Qdrant vectors for document_id=%s: %s", doc.id, exc)

    db.delete(session)
    db.commit()
    return None

@router.post("/{session_id}/chat", response_model=ChatMessageResponse)
async def chat_with_documents(
    session_id: UUID,
    request: ChatRequest,
    db: Session = Depends(get_db),
    embedding_service: BaseEmbeddingService = Depends(get_embedding_service),
    llm_service: BaseLLMService = Depends(get_llm_service)
):
    """The main RAG endpoint. Takes a question, searches docs, and returns AI answer."""
    
    session = ChatSessionRepository.get_by_id(db=db, session_id=session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    user_message = ChatMessageRepository.create(
        db=db,
        session_id=session_id,
        role="user",
        content=request.message
    )
    
    context = RetrievalService.get_context_for_query(
        db=db,
        session_id=session_id,
        query=request.message,
        embedding_service=embedding_service,
        limit=5
    )
    
    raw_history = ChatMessageRepository.get_recent_by_session(db=db, session_id=session_id, limit=6)

    formatted_history = [
        {"role": msg.role, "content": msg.content} 
        for msg in raw_history[:-1] 
    ]
    
    system_prompt = (
        "You are AskMyDoc, a highly intelligent and helpful AI assistant. "
        "Your goal is to answer the user's question accurately based STRICTLY on the provided CONTEXT. "
        "If the answer is not contained within the CONTEXT, explicitly state that you do not have enough information to answer. "
        "Do not invent, hallucinate, or rely on outside knowledge."
    )
    
    try:
        ai_response_text = llm_service.generate_answer(
            system_prompt=system_prompt,
            context=context,
            history=formatted_history,
            question=request.message
        )
    except LLMUnavailableError as exc:
        logger.warning("LLM unavailable for session_id=%s: %s", session_id, exc)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="The AI model is busy right now. Please try again in a few seconds.",
        ) from exc

    ai_message = ChatMessageRepository.create(
        db=db,
        session_id=session_id,
        role="assistant",
        content=ai_response_text
    )

    # Auto-name the session from its first exchange, unless the user already
    # named it. `formatted_history` is empty only on the first message.
    is_first_message = len(formatted_history) == 0
    if is_first_message and session.title == DEFAULT_SESSION_TITLE:
        try:
            generated = llm_service.generate_title(request.message, ai_response_text)
            title = _clean_title(generated)
        except Exception as exc:
            logger.warning("Title generation failed for session_id=%s: %s", session_id, exc)
            title = ""
        title = title or _fallback_title(request.message)
        ChatSessionRepository.update_title(db=db, session=session, title=title)

    return ai_message