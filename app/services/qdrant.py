import logging
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
        