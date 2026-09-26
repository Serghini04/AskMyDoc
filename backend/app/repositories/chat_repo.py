from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.chat import ChatMessage, ChatSession


class ChatSessionRepository:
    """Data access for chat sessions. Never commits — the caller owns the transaction."""

    def __init__(self, db: Session):
        self.db = db

    def add(self, chat_session: ChatSession) -> ChatSession:
        self.db.add(chat_session)
        self.db.flush()
        return chat_session

    def get(self, session_id: UUID) -> ChatSession | None:
        return self.db.get(ChatSession, session_id)

    def list_page(self, *, offset: int, limit: int) -> list[ChatSession]:
        stmt = (
            select(ChatSession).order_by(ChatSession.created_at.desc()).offset(offset).limit(limit)
        )
        return list(self.db.scalars(stmt))

    def delete(self, chat_session: ChatSession) -> None:
        self.db.delete(chat_session)


class ChatMessageRepository:
    """Data access for chat messages. Never commits — the caller owns the transaction."""

    def __init__(self, db: Session):
        self.db = db

    def add(self, message: ChatMessage) -> ChatMessage:
        self.db.add(message)
        self.db.flush()
        return message

    def recent(self, session_id: UUID, limit: int) -> list[ChatMessage]:
        """The last `limit` messages of a session, oldest first."""
        stmt = (
            select(ChatMessage)
            .where(ChatMessage.session_id == session_id)
            .order_by(ChatMessage.created_at.desc())
            .limit(limit)
        )
        return list(reversed(self.db.scalars(stmt).all()))
