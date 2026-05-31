import logging
from abc import ABC, abstractmethod
from functools import lru_cache
from typing import List

from fastembed import TextEmbedding

from app.config import settings


class BaseEmbeddingService(ABC):
    @abstractmethod
    def embed_text(self, text: str) -> List[float]:
        pass


class FastEmbedService(BaseEmbeddingService):
    def __init__(self):
        logging.info("Loading embedding model: %s", settings.FASTEMBED_MODEL)
        self._model = TextEmbedding(model_name=settings.FASTEMBED_MODEL)
        logging.info("Embedding model ready.")

    def embed_text(self, text: str) -> List[float]:
        embeddings = list(self._model.embed([text]))
        return embeddings[0].tolist()


@lru_cache(maxsize=1)
def get_embedding_service() -> BaseEmbeddingService:
    return FastEmbedService()
