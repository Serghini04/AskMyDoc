import logging
from functools import lru_cache
from qdrant_client import QdrantClient
from qdrant_client.http import models
from app.config import settings

class QdrantService:
    def __init__(self):
        self.client = QdrantClient(url=settings.QDRANT_URL)
        self.collection_name = "document_chunks"
        self._ensure_collection_exists()
        
    def _ensure_collection_exists(self):
        """
        Checks if the collection exists. If not, it creates it with the
        exact dimensions needed for BGE-M3 (1024)
        """
        collections = self.client.get_collections().collections
        exists = any(col.name == self.collection_name for col in collections)
        
        if not exists:
            logging.info(f"Creating Qdrant collection: {self.collection_name}")
            self.client.create_collection(
                collection_name=self.collection_name,
                vectors_config=models.VectorParams(
                    size=1024,
                    distance=models.Distance.COSINE
                )
            )
            logging.info("Collection created successfully.")
            
    def upsert_points(self, points: list[dict]):
        """
        Takes our mapped payloads and saves them into the Vector Database.
        """
        qdrant_points = [
            models.PointStruct(
                id=point["id"],
                vector=point["vector"],
                payload=point["payload"]
            )
            for point in points
        ]
        
        operation_info = self.client.upsert(
            collection_name=self.collection_name,
            wait=True,
            points=qdrant_points
        )
        
        logging.info(f"Successfully upserted {len(points)} vectors to Qdrant.")
    
    def search_similar_chunks(self, query_vector: list[float], session_id: str, limit: int = 5):
        """
        Searches for the most similar vectors, filtered directly by session_id.
        This seamlessly handles 1 file or 100 files inside the same chat session!
        """
        doc_filter = models.Filter(
            must=[
                models.FieldCondition(
                    key="session_id",
                    match=models.MatchValue(value=session_id)
                )
            ]
        )

        search_results = self.client.search(
            collection_name=self.collection_name,
            query_vector=query_vector,
            query_filter=doc_filter,
            limit=limit
        )

        logging.info(f"Retrieved {len(search_results)} chunks from Qdrant.")
        return search_results

    def delete_points_by_document(self, document_id: str) -> None:
        """Delete all vectors for a document using its payload filter."""
        doc_filter = models.Filter(
            must=[
                models.FieldCondition(
                    key="document_id",
                    match=models.MatchValue(value=document_id)
                )
            ]
        )

        self.client.delete(
            collection_name=self.collection_name,
            points_selector=models.FilterSelector(filter=doc_filter),
            wait=True
        )

        logging.info("Deleted vectors for document_id=%s", document_id)


@lru_cache(maxsize=1)
def get_qdrant_service() -> QdrantService:
    return QdrantService()