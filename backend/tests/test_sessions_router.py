import uuid

from app.services import storage


def test_create_session(api_client):
    response = api_client.post("/api/v1/sessions/")
    assert response.status_code == 201
    payload = response.json()
    assert payload["title"] == "New Chat"
    assert payload["messages"] == []
    assert payload["documents"] == []


def test_list_sessions_newest_first(api_client):
    first = api_client.post("/api/v1/sessions/").json()["id"]
    second = api_client.post("/api/v1/sessions/").json()["id"]

    response = api_client.get("/api/v1/sessions/")
    assert response.status_code == 200
    assert [s["id"] for s in response.json()] == [second, first]


def test_get_session_found_and_not_found(api_client):
    session_id = api_client.post("/api/v1/sessions/").json()["id"]
    assert api_client.get(f"/api/v1/sessions/{session_id}").json()["id"] == session_id

    missing = api_client.get(f"/api/v1/sessions/{uuid.uuid4()}")
    assert missing.status_code == 404
    assert missing.json() == {"detail": "Session not found"}


def test_get_session_rejects_malformed_id(api_client):
    assert api_client.get("/api/v1/sessions/not-a-uuid").status_code == 422


def test_rename_session(api_client):
    session_id = api_client.post("/api/v1/sessions/").json()["id"]

    response = api_client.patch(f"/api/v1/sessions/{session_id}", json={"title": "  Q&A  "})
    assert response.status_code == 200
    assert response.json()["title"] == "Q&A"
    # Persisted, not just echoed back.
    assert api_client.get(f"/api/v1/sessions/{session_id}").json()["title"] == "Q&A"


def test_rename_session_not_found(api_client):
    response = api_client.patch(f"/api/v1/sessions/{uuid.uuid4()}", json={"title": "nope"})
    assert response.status_code == 404


def test_rename_session_rejects_empty_title(api_client):
    session_id = api_client.post("/api/v1/sessions/").json()["id"]
    response = api_client.patch(f"/api/v1/sessions/{session_id}", json={"title": "   "})
    assert response.status_code == 422  # stripped to empty -> fails min_length


def test_delete_session_removes_everything(api_client, fake_qdrant):
    session_id = api_client.post("/api/v1/sessions/").json()["id"]
    doc_id = api_client.post(
        "/api/v1/documents/",
        data={"session_id": session_id},
        files={"file": ("note.txt", b"hello", "text/plain")},
    ).json()["id"]
    stored = storage.stored_file_path(uuid.UUID(doc_id), "note.txt")
    assert stored.exists()

    assert api_client.delete(f"/api/v1/sessions/{session_id}").status_code == 204

    # The session's documents lose their files and vectors too.
    assert not stored.exists()
    assert fake_qdrant.deleted_documents == [uuid.UUID(doc_id)]
    assert api_client.get(f"/api/v1/sessions/{session_id}").status_code == 404
    assert api_client.get(f"/api/v1/documents/{doc_id}").status_code == 404


def test_delete_session_not_found(api_client):
    assert api_client.delete(f"/api/v1/sessions/{uuid.uuid4()}").status_code == 404
