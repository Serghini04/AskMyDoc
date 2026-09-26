import mimetypes
from dataclasses import dataclass
from pathlib import Path
from typing import BinaryIO
from uuid import UUID

from sqlalchemy.orm import Session

from app.config import settings
from app.exceptions import (
    ConflictError,
    InvalidRequestError,
    NotFoundError,
    UnsupportedMediaTypeError,
)
from app.models.document import Document
from app.repositories.chat_repo import ChatSessionRepository
from app.repositories.document_repo import DocumentRepository
from app.services import ingestion, storage


@dataclass(frozen=True)
class DownloadableFile:
    path: Path
    filename: str
    media_type: str


class DocumentService:
    """Document use cases. Each public method is one transaction."""

    def __init__(self, db: Session):
        self.db = db
        self.documents = DocumentRepository(db)
        self.sessions = ChatSessionRepository(db)

    def upload(self, session_id: UUID, filename: str, content: BinaryIO) -> Document:
        """
        Validate and store an upload as a PENDING document. The caller schedules
        ingestion afterwards (`ingestion.ingest_document`).
        """
        extension = storage.file_extension(filename)
        if extension not in storage.ALLOWED_EXTENSIONS:
            raise UnsupportedMediaTypeError(
                f"Unsupported file type: {extension or '(none)'}. Only PDF and TXT are allowed."
            )

        staged = storage.stage_upload(content, settings.max_upload_bytes)
        stored_path: Path | None = None
        try:
            if self.sessions.get(session_id) is None:
                raise InvalidRequestError("session_id does not exist")

            existing = self.documents.find_in_session_by_hash(session_id, staged.sha256)
            if existing is not None:
                raise ConflictError(f"File already exists with ID: {existing.id}")

            document = self.documents.add(
                Document(
                    filename=filename,
                    file_hash=staged.sha256,
                    file_size_bytes=staged.size_bytes,
                    session_id=session_id,
                )
            )
            stored_path = storage.promote(staged, document.id, filename)
            self.db.commit()
        except BaseException:
            self.db.rollback()
            storage.discard(stored_path or staged.temp_path)
            raise
        return document

    def get(self, document_id: UUID) -> Document:
        document = self.documents.get(document_id)
        if document is None:
            raise NotFoundError("Document not found")
        return document

    def list_documents(self, *, offset: int, limit: int) -> list[Document]:
        return self.documents.list_page(offset=offset, limit=limit)

    def delete(self, document_id: UUID) -> None:
        document = self.get(document_id)
        filename = document.filename
        self.documents.delete(document)
        self.db.commit()
        ingestion.purge_document_artifacts(document_id, filename)

    def download(self, document_id: UUID) -> DownloadableFile:
        document = self.get(document_id)
        path = storage.stored_file_path(document.id, document.filename)
        if not path.exists():
            raise NotFoundError("Physical file is missing from the server")
        media_type, _ = mimetypes.guess_type(document.filename)
        return DownloadableFile(
            path=path,
            filename=document.filename,
            media_type=media_type or "application/octet-stream",
        )
