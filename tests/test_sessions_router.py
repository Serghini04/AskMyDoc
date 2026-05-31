from app.api.routers import documents
from app.services import retrieval


def test_create_session(api_client):
    response = api_client.post("/api/v1/sessions/")
    assert response.status_code == 201
    payload = response.json()
    assert "id" in payload
    assert payload["title"] == "New Chat"
    assert payload["messages"] == []
    assert payload["documents"] == []


def test_list_sessions(api_client):
    api_client.post("/api/v1/sessions/")
    api_client.post("/api/v1/sessions/")

    response = api_client.get("/api/v1/sessions/")
    assert response.status_code == 200
    assert len(response.json()) >= 2


def test_get_session_found(api_client):
    created = api_client.post("/api/v1/sessions/").json()
    session_id = created["id"]

    response = api_client.get(f"/api/v1/sessions/{session_id}")
    assert response.status_code == 200
    assert response.json()["id"] == session_id


def test_get_session_not_found(api_client):
    import uuid
    response = api_client.get(f"/api/v1/sessions/{uuid.uuid4()}")
    assert response.status_code == 404


def test_delete_session_removes_session_and_returns_204(api_client, monkeypatch):
    monkeypatch.setattr(documents, "process_document_background", lambda *_a, **_kw: None)
    monkeypatch.setattr(
        retrieval.RetrievalService,
        "get_context_for_query",
        lambda *_a, **_kw: "ctx",
    )

    session_id = api_client.post("/api/v1/sessions/").json()["id"]

    api_client.post(
        "/api/v1/documents/",
        data={"session_id": session_id},
        files={"file": ("note.txt", b"hello", "text/plain")},
    )

    delete_response = api_client.delete(f"/api/v1/sessions/{session_id}")
    assert delete_response.status_code == 204

    get_response = api_client.get(f"/api/v1/sessions/{session_id}")
    assert get_response.status_code == 404


def test_delete_session_not_found(api_client):
    import uuid
    response = api_client.delete(f"/api/v1/sessions/{uuid.uuid4()}")
    assert response.status_code == 404


def test_upload_rejects_oversized_file(api_client, monkeypatch, session_maker):
    from app.config import settings
    from app.models.chat import ChatSession

    monkeypatch.setattr(settings, "MAX_UPLOAD_SIZE_MB", 0)

    db = session_maker()
    chat_session = ChatSession(title="size test")
    db.add(chat_session)
    db.commit()
    db.refresh(chat_session)
    session_id = str(chat_session.id)
    db.close()

    response = api_client.post(
        "/api/v1/documents/",
        data={"session_id": session_id},
        files={"file": ("big.txt", b"x" * 1, "text/plain")},
    )
    assert response.status_code == 413  # HTTP 413 Content Too Large
