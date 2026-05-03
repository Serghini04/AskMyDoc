from app.api.routers import documents
from app.services import retrieval


def test_upload_and_chat_flow(api_client, monkeypatch):
    monkeypatch.setattr(documents, "process_document_background", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(
        retrieval.RetrievalService,
        "get_context_for_query",
        lambda *_args, **_kwargs: "context",
    )

    session_response = api_client.post("/api/v1/sessions/")
    assert session_response.status_code == 201
    session_id = session_response.json()["id"]

    upload_response = api_client.post(
        "/api/v1/documents/",
        data={"session_id": session_id},
        files={"file": ("note.txt", b"hello", "text/plain")},
    )
    assert upload_response.status_code == 201
    doc_id = upload_response.json()["id"]

    chat_response = api_client.post(
        f"/api/v1/sessions/{session_id}/chat",
        json={"message": "What is this?"},
    )
    assert chat_response.status_code == 200

    session_detail = api_client.get(f"/api/v1/sessions/{session_id}")
    assert session_detail.status_code == 200
    payload = session_detail.json()
    assert payload["documents"][0]["id"] == doc_id
    assert len(payload["messages"]) == 2
