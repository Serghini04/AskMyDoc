from collections.abc import Iterable
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.document import Document
from app.models.enums import DocumentStatus


class DocumentRepository:
    """Data access for documents. Never commits — the caller owns the transaction."""

    def __init__(self, db: Session):
        self.db = db

    def add(self, document: Document) -> Document:
        self.db.add(document)
        self.db.flush()
        return document

    def get(self, document_id: UUID) -> Document | None:
        return self.db.get(Document, document_id)

    def list_page(self, *, offset: int, limit: int) -> list[Document]:
        stmt = select(Document).order_by(Document.created_at.desc()).offset(offset).limit(limit)
        return list(self.db.scalars(stmt))

    def find_in_session_by_hash(self, session_id: UUID, file_hash: str) -> Document | None:
        stmt = select(Document).where(
            Document.session_id == session_id, Document.file_hash == file_hash
        )
        return self.db.scalars(stmt).first()

    def list_with_status(self, statuses: Iterable[DocumentStatus]) -> list[Document]:
        stmt = select(Document).where(Document.status.in_(list(statuses)))
        return list(self.db.scalars(stmt))

    def set_all_statuses(self, status: DocumentStatus) -> None:
        for document in self.db.scalars(select(Document)):
            document.status = status

    def delete(self, document: Document) -> None:
        self.db.delete(document)
