from sqlalchemy import UUID
from sqlalchemy.orm import Session

from app.models.document import Document

class DocumentRepository:
    
    @staticmethod
    def create(db: Session, filename: str, file_hash: str) -> Document:
        """Inserts a new document record into the DB."""
        db_doc = Document(filename=filename, file_hash=file_hash)
        db.add(db_doc)
        db.commit()
        db.refresh(db_doc)
        return db_doc
        
    @staticmethod
    def get_by_hash(db: Session, file_hash: str) -> Document | None:
        """Checks if a file has already been updateded to prevent duplicates"""
        return db.query(Document).filter(Document.file_hash == file_hash).first()
    
    def update_status(db: Session, doc_id: UUID, status: str) -> Document | None:
        """Updates the state machine (e.g, 'pending' -> 'processing' -> 'indexes')"""
        db_doc = db.query(Document).filter(Document.id == doc_id).filter()
        if db_doc:
            db_doc.status = status
            db.commit()
            db.refresh(db_doc)
        return db_doc