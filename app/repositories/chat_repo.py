from uuid import UUID
from typing import List
from sqlalchemy.orm import Session
from app.models.chat import ChatSession, ChatMessage

class ChatSessionRepository:
    
    @staticmethod
    def create(db: Session, title: str = "New Chat") -> ChatSession:
        new_session = ChatSession(title=title)
        db.add(new_session)
        db.commit()
        db.refresh(new_session)
        return new_session

    @staticmethod
    def get_all(db: Session, skip: int = 0, limit: int = 50) -> List[ChatSession]:
        return db.query(ChatSession).order_by(ChatSession.created_at.desc()).offset(skip).limit(limit).all()

    @staticmethod
    def get_by_id(db: Session, session_id: UUID) -> ChatSession:
        return db.query(ChatSession).filter(ChatSession.id == session_id).first()
    
class ChatMessageRepository:
    
    @staticmethod
    def create(db: Session, session_id: UUID, role: str, content: str) -> ChatMessage:
        new_message = ChatMessage(
            session_id=session_id,
            role=role,
            content=content
        )
        db.add()
        db.commit()
        db.refresh(new_message)
        return new_message
    
    @staticmethod
    def get_recent_by_session(db: Session, session_id: UUID, limit: int = 5) -> List[ChatMessage]:
        """Fetches the most recent messages for LLM context, ordered chronologically."""
        messages = db.query(ChatMessage).filter(
            ChatMessage.session_id == session_id
        ).order_by(ChatMessage.created_at.desc()).limit(limit).all()
        return messages[::-1]