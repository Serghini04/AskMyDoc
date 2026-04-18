import uuid

from sqlalchemy import UUID
from sqlalchemy.orm import Session

from app.models.chat import ChatSession
from app.models.document import Document

class DocumentRepository:
    
    @staticmethod
    def create(
        db: Session,
        filename: str,
        file_hash: str,
        session_id: uuid.UUID | None = None,
    ) -> Document:
        """Inserts a new document record into the DB."""
        if session_id is None:
            raise ValueError("session_id is required")

        session = db.query(ChatSession).filter(ChatSession.id == session_id).first()
        if session is None:
            raise ValueError("session_id does not exist")

        db_doc = Document(filename=filename, file_hash=file_hash, session_id=session_id)
        db.add(db_doc)
        db.commit()
        db.refresh(db_doc)
        return db_doc
        
    @staticmethod
    def get_by_hash(db: Session, file_hash: str) -> Document | None:
        """Checks if a file has already been updateded to prevent duplicates"""
        return db.query(Document).filter(Document.file_hash == file_hash).first()
    
    @staticmethod
    def update_status(db: Session, doc_id: UUID, status: str) -> Document | None:
        """Updates the state machine (e.g, 'pending' -> 'processing' -> 'indexes')"""
        db_doc = db.query(Document).filter(Document.id == doc_id).first()
        if db_doc:
            db_doc.status = status
            db.commit()
            db.refresh(db_doc)
        return db_doc