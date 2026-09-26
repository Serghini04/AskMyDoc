"""
Full RAG flow with real ingestion and retrieval code; only the external
services (embeddings, LLM, Qdrant) are fakes.
"""

import uuid

from app.services import ingestion
from app.services.ingestion import ingest_document  # bound before fixtures patch it
from tests.conftest import DummyEmbeddingService


def test_upload_ingest_then_answer_from_document(api_client, session_maker, monkeypatch, llm):
    session_id = api_client.post("/api/v1/sessions/").json()["id"]
    doc_id = api_client.post(
        "/api/v1/documents/",
        data={"session_id": session_id},
        files={"file": ("memo.txt", b"The Orion launch is on 9 May 2031.", "text/plain")},
    ).json()["id"]

    # Run the real ingestion pipeline against the test database.
    monkeypatch.setattr(ingestion, "SessionLocal", session_maker)
    ingest_document(uuid.UUID(doc_id), embeddings=DummyEmbeddingService())
    assert api_client.get(f"/api/v1/documents/{doc_id}").json()["status"] == "COMPLETED"

    answer = api_client.post(
        f"/api/v1/sessions/{session_id}/chat", json={"message": "When is the launch?"}
    )
    assert answer.status_code == 200
    # Retrieval found the document's text and handed it to the LLM.
    assert "9 May 2031" in llm.contexts[-1]

    detail = api_client.get(f"/api/v1/sessions/{session_id}").json()
    assert detail["documents"][0]["id"] == doc_id
    assert len(detail["messages"]) == 2


def test_chat_without_documents_gets_empty_context(api_client, llm):
    session_id = api_client.post("/api/v1/sessions/").json()["id"]
    api_client.post(f"/api/v1/sessions/{session_id}/chat", json={"message": "anything?"})
    assert llm.contexts == [""]
