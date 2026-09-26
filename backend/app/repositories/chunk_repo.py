from collections.abc import Sequence
from uuid import UUID

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.models.document import Chunk


class ChunkRepository:
    """Data access for document chunks. Never commits — the caller owns the transaction."""

    def __init__(self, db: Session):
        self.db = db

    def add_all(self, document_id: UUID, texts: Sequence[str]) -> list[Chunk]:
        chunks = [
            Chunk(document_id=document_id, chunk_index=index, content=text)
            for index, text in enumerate(texts)
        ]
        self.db.add_all(chunks)
        self.db.flush()  # assigns IDs, which become the Qdrant point IDs
        return chunks

    def delete_for_document(self, document_id: UUID) -> None:
        self.db.execute(delete(Chunk).where(Chunk.document_id == document_id))

    def contents_by_id(self, chunk_ids: Sequence[UUID]) -> dict[UUID, str]:
        stmt = select(Chunk.id, Chunk.content).where(Chunk.id.in_(chunk_ids))
        return {chunk_id: content for chunk_id, content in self.db.execute(stmt)}
