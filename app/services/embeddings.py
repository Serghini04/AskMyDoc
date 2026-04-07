import torch
from abc import ABC, abstractmethod
from typing import List
from sentence_transformers import SentenceTransformer

class BaseEmbeddingService(ABC):
    @abstractmethod
    def embed_text(self, text: str) -> List[float]:
        pass

class BGEM3EmbeddingService(BaseEmbeddingService):
    def __init__(self):
        device = "cuda" if torch.cuda.is_available() else "cpu"
        print(f"Loading BGE-M3 model into memory on {device.upper()}...")
        
        self.model = SentenceTransformer('BAAI/bge-m3', device=device)
        print("BGE-M3 model loaded successfully!")

    def embed_text(self, text: str) -> List[float]:
        embedding = self.model.encode(text)
        return embedding.tolist()