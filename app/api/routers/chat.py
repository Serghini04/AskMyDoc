from uuid import UUID
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.dependencies import get_db, get_embedding_service
from app.services.embeddings import BaseEmbeddingService
from app.schemas.chat import ChatSessionResponse, ChatRequest, ChatMessageResponse
from app.repositories.chat_repo import ChatSessionRepository, ChatMessageRepository

router = APIRouter(prefix="/sessions", tags=["Chat Sessions"])

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

@router.post("/{session_id}/chat", response_model=ChatMessageResponse)
async def chat_with_documents(
    session_id: UUID,
    request: ChatRequest,
    db: Session = Depends(get_db),
    embedding_service: BaseEmbeddingService = Depends(get_embedding_service)
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

    # TODO: 2. Embed the user's question using embedding_service
    # TODO: 3. Query Qdrant for context (Filtered by this session_id!)
    # TODO: 4. Fetch the last 5 messages via ChatMessageRepository for chat memory
    # TODO: 5. Construct the Prompt (System + Context + History + Question)
    # TODO: 6. Call the LLM (OpenAI/Anthropic) synchronously
    # TODO: 7. Save the LLM's response via ChatMessageRepository (role="assistant")
    
    # Placeholder return so the app doesn't crash right now
    dummy_response = ChatMessageRepository.create(
        db=db,
        session_id=session_id,
        role="assistant",
        content="I am ready to be wired up to Qdrant and the LLM!"
    )
    return dummy_response