from uuid import UUID

from sqlalchemy.orm import Session

from app.config import settings
from app.repositories.chunk_repo import ChunkRepository
from app.services import qdrant
from app.services.embeddings import BaseEmbeddingService

CONTEXT_SEPARATOR = "\n\n---\n\n"


class RetrievalService:
    """
    Retrieval with the pointer method:
    1. embed the question, 2. search Qdrant for chunk IDs (scoped to the session),
    3. fetch the chunk text from Postgres, preserving Qdrant's ranking.
    """

    def __init__(self, db: Session, embeddings: BaseEmbeddingService):
        self.chunks = ChunkRepository(db)
        self.embeddings = embeddings

    def retrieve_context(self, session_id: UUID, query: str) -> str:
        """The most relevant chunks joined into one context string ("" if none)."""
        query_vector = self.embeddings.embed_text(query)
        chunk_ids = qdrant.get_qdrant_service().search_chunk_ids(
            query_vector, session_id, limit=settings.RETRIEVAL_TOP_K
        )
        if not chunk_ids:
            return ""

        contents = self.chunks.contents_by_id(chunk_ids)
        # A vector whose chunk row is gone (e.g. mid-deletion) is skipped.
        return CONTEXT_SEPARATOR.join(contents[cid] for cid in chunk_ids if cid in contents)
