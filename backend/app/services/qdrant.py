import logging
from collections.abc import Sequence
from dataclasses import dataclass
from functools import lru_cache
from uuid import UUID

from qdrant_client import QdrantClient
from qdrant_client.http import models

from app.config import settings

logger = logging.getLogger(__name__)

# Keeps each upsert request well under Qdrant's 32MB request limit.
UPSERT_BATCH_SIZE = 256


class EmbeddingDimensionMismatchError(RuntimeError):
    """The collection was built for a different embedding model."""


@dataclass(frozen=True)
class ChunkPoint:
    """A chunk's vector plus the metadata needed to filter searches.

    The point ID is the chunk's Postgres ID: the vector store holds no text,
    and every search hit points back to its row (Postgres stays the source of truth).
    """

    chunk_id: UUID
    document_id: UUID
    session_id: UUID
    chunk_index: int
    vector: list[float]


class QdrantService:
    def __init__(self, check_dimensions: bool = True) -> None:
        self.client = QdrantClient(url=settings.QDRANT_URL)
        self.collection_name = settings.QDRANT_COLLECTION
        self._ensure_collection_exists(check_dimensions)

    # --- collection lifecycle -------------------------------------------------

    def collection_dimensions(self) -> int:
        return self.client.get_collection(self.collection_name).config.params.vectors.size

    def recreate_collection(self) -> None:
        """Drop every vector and recreate the collection at the configured size."""
        self.client.delete_collection(self.collection_name)
        self._create_collection()

    def _ensure_collection_exists(self, check_dimensions: bool) -> None:
        existing = {col.name for col in self.client.get_collections().collections}
        if self.collection_name not in existing:
            self._create_collection()
            return

        size = self.collection_dimensions()
        if check_dimensions and size != settings.EMBEDDING_DIMENSIONS:
            # Mixing vector sizes would break every search — fail loudly instead.
            raise EmbeddingDimensionMismatchError(
                f"Qdrant collection '{self.collection_name}' holds {size}-dim vectors but "
                f"EMBEDDING_DIMENSIONS={settings.EMBEDDING_DIMENSIONS}. "
                "Run `make reindex` after changing the embedding model."
            )

    def _create_collection(self) -> None:
        logger.info(
            "Creating Qdrant collection %s (%d dims)",
            self.collection_name,
            settings.EMBEDDING_DIMENSIONS,
        )
        self.client.create_collection(
            collection_name=self.collection_name,
            vectors_config=models.VectorParams(
                size=settings.EMBEDDING_DIMENSIONS,
                distance=models.Distance.COSINE,
            ),
        )

    # --- points ---------------------------------------------------------------

    def upsert_chunks(self, points: Sequence[ChunkPoint]) -> None:
        structs = [
            models.PointStruct(
                id=str(point.chunk_id),
                vector=point.vector,
                payload={
                    "document_id": str(point.document_id),
                    "session_id": str(point.session_id),
                    "chunk_index": point.chunk_index,
                },
            )
            for point in points
        ]
        for start in range(0, len(structs), UPSERT_BATCH_SIZE):
            self.client.upsert(
                collection_name=self.collection_name,
                points=structs[start : start + UPSERT_BATCH_SIZE],
                wait=True,
            )
        logger.info("Upserted %d vectors", len(structs))

    def search_chunk_ids(
        self, query_vector: list[float], session_id: UUID, limit: int
    ) -> list[UUID]:
        """IDs of the chunks most similar to the query within one session, best first."""
        hits = self.client.query_points(
            collection_name=self.collection_name,
            query=query_vector,
            query_filter=_match("session_id", session_id),
            limit=limit,
        ).points
        return [UUID(str(hit.id)) for hit in hits]

    def delete_document(self, document_id: UUID) -> None:
        self.client.delete(
            collection_name=self.collection_name,
            points_selector=models.FilterSelector(filter=_match("document_id", document_id)),
            wait=True,
        )


def _match(key: str, value: UUID) -> models.Filter:
    return models.Filter(
        must=[models.FieldCondition(key=key, match=models.MatchValue(value=str(value)))]
    )


@lru_cache(maxsize=1)
def get_qdrant_service() -> QdrantService:
    return QdrantService()
