from types import SimpleNamespace

import pytest

from app.config import settings
from app.services import qdrant as qdrant_module
from app.services.qdrant import EmbeddingDimensionMismatchError, QdrantService


class FakeClient:
    def __init__(self, existing_size=None):
        self.size = existing_size
        self.created = []
        self.deleted = []

    def get_collections(self):
        names = [] if self.size is None else [SimpleNamespace(name="document_chunks")]
        return SimpleNamespace(collections=names)

    def get_collection(self, name):
        vectors = SimpleNamespace(size=self.size)
        return SimpleNamespace(config=SimpleNamespace(params=SimpleNamespace(vectors=vectors)))

    def create_collection(self, collection_name, vectors_config):
        self.size = vectors_config.size
        self.created.append(vectors_config.size)

    def delete_collection(self, name):
        self.deleted.append(name)
        self.size = None


def _install(monkeypatch, client):
    monkeypatch.setattr(qdrant_module, "QdrantClient", lambda url: client)


def test_creates_collection_with_configured_dimensions(monkeypatch):
    client = FakeClient(existing_size=None)
    _install(monkeypatch, client)
    QdrantService()
    assert client.created == [settings.EMBEDDING_DIMENSIONS]


def test_refuses_collection_built_for_another_model(monkeypatch):
    _install(monkeypatch, FakeClient(existing_size=settings.EMBEDDING_DIMENSIONS + 1))
    with pytest.raises(EmbeddingDimensionMismatchError, match="make reindex"):
        QdrantService()


def test_recreate_collection_fixes_mismatch(monkeypatch):
    client = FakeClient(existing_size=384)
    _install(monkeypatch, client)
    service = QdrantService(check_dimensions=False)
    service.recreate_collection()
    assert client.deleted == ["document_chunks"]
    assert service.collection_dimensions() == settings.EMBEDDING_DIMENSIONS
