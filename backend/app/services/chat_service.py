import logging
from uuid import UUID

from sqlalchemy.orm import Session

from app.config import settings
from app.exceptions import NotFoundError
from app.models.chat import DEFAULT_SESSION_TITLE, ChatMessage, ChatSession
from app.models.enums import MessageRole
from app.repositories.chat_repo import ChatMessageRepository, ChatSessionRepository
from app.services import ingestion
from app.services.embeddings import BaseEmbeddingService
from app.services.llm import BaseLLMService, ChatTurn
from app.services.retrieval import RetrievalService

logger = logging.getLogger(__name__)

MAX_TITLE_LENGTH = 255
FALLBACK_TITLE_WORDS = 6


class ChatService:
    """Chat session use cases. Each public method is one transaction."""

    def __init__(self, db: Session, llm: BaseLLMService, embeddings: BaseEmbeddingService):
        self.db = db
        self.llm = llm
        self.sessions = ChatSessionRepository(db)
        self.messages = ChatMessageRepository(db)
        self.retrieval = RetrievalService(db, embeddings)

    # --- sessions -------------------------------------------------------------

    def create_session(self) -> ChatSession:
        chat_session = self.sessions.add(ChatSession(title=DEFAULT_SESSION_TITLE))
        self.db.commit()
        return chat_session

    def list_sessions(self, *, offset: int, limit: int) -> list[ChatSession]:
        return self.sessions.list_page(offset=offset, limit=limit)

    def get_session(self, session_id: UUID) -> ChatSession:
        chat_session = self.sessions.get(session_id)
        if chat_session is None:
            raise NotFoundError("Session not found")
        return chat_session

    def rename_session(self, session_id: UUID, title: str) -> ChatSession:
        chat_session = self.get_session(session_id)
        chat_session.title = title
        self.db.commit()
        return chat_session

    def delete_session(self, session_id: UUID) -> None:
        """Delete a session with its messages, documents, chunks, vectors, and files."""
        chat_session = self.get_session(session_id)
        documents = [(doc.id, doc.filename) for doc in chat_session.documents]
        self.sessions.delete(chat_session)
        self.db.commit()
        for document_id, filename in documents:
            ingestion.purge_document_artifacts(document_id, filename)

    # --- RAG ------------------------------------------------------------------

    def ask(self, session_id: UUID, question: str) -> ChatMessage:
        """
        Answer a question from the session's documents. Provider calls run
        before any write, so a failure (ProviderUnavailableError) leaves the
        conversation untouched and Retry doesn't duplicate the question.
        """
        chat_session = self.get_session(session_id)
        history: list[ChatTurn] = [
            {"role": message.role, "content": message.content}
            for message in self.messages.recent(session_id, settings.CHAT_HISTORY_MESSAGES)
        ]

        context = self.retrieval.retrieve_context(session_id, question)
        answer = self.llm.generate_answer(context, history, question)

        # Name the session from its first exchange, unless the user already named it.
        if not history and chat_session.title == DEFAULT_SESSION_TITLE:
            chat_session.title = self._generate_title(question, answer)

        self.messages.add(
            ChatMessage(session_id=session_id, role=MessageRole.USER, content=question)
        )
        reply = self.messages.add(
            ChatMessage(session_id=session_id, role=MessageRole.ASSISTANT, content=answer)
        )
        self.db.commit()
        return reply

    def _generate_title(self, question: str, answer: str) -> str:
        try:
            title = _clean_title(self.llm.generate_title(question, answer))
        except Exception:
            # A missing title must never fail the user's question.
            logger.warning("Title generation failed", exc_info=True)
            title = ""
        return title or _fallback_title(question)


def _clean_title(raw: str) -> str:
    """Normalize an LLM-generated title: first line, unquoted, length-capped."""
    lines = raw.strip().splitlines()
    if not lines:
        return ""
    return lines[0].strip().strip("\"“”'")[:MAX_TITLE_LENGTH].strip()


def _fallback_title(question: str) -> str:
    words = question.split()[:FALLBACK_TITLE_WORDS]
    return " ".join(words)[:MAX_TITLE_LENGTH].strip() or DEFAULT_SESSION_TITLE
