import uuid

from app.config import settings

PDF_OR_TXT_ONLY = "Only PDF and TXT are allowed"


def _new_session(api_client) -> str:
    return api_client.post("/api/v1/sessions/").json()["id"]


def _upload(api_client, session_id, name="contract.txt", content=b"hello from test"):
    return api_client.post(
        "/api/v1/documents/",
        data={"session_id": session_id},
        files={"file": (name, content, "text/plain")},
    )


def test_upload_list_get_download_delete_full_flow(api_client, ingest_calls, fake_qdrant):
    session_id = _new_session(api_client)

    response = _upload(api_client, session_id)
    assert response.status_code == 201
    payload = response.json()
    doc_id = payload["id"]
    assert payload["filename"] == "contract.txt"
    assert payload["status"] == "PENDING"
    assert payload["file_size_bytes"] == len(b"hello from test")
    assert ingest_calls == [uuid.UUID(doc_id)]

    listed = api_client.get("/api/v1/documents/")
    assert listed.status_code == 200
    assert [d["id"] for d in listed.json()] == [doc_id]

    assert api_client.get(f"/api/v1/documents/{doc_id}").json()["id"] == doc_id

    download = api_client.get(f"/api/v1/documents/{doc_id}/download")
    assert download.status_code == 200
    assert download.content == b"hello from test"
    assert download.headers["content-type"].startswith("text/plain")

    assert api_client.delete(f"/api/v1/documents/{doc_id}").status_code == 204
    assert api_client.get(f"/api/v1/documents/{doc_id}").status_code == 404
    assert fake_qdrant.deleted_documents == [uuid.UUID(doc_id)]


def test_upload_rejects_duplicate_by_hash_per_session(api_client, upload_dir):
    session_id = _new_session(api_client)
    other_session_id = _new_session(api_client)

    assert _upload(api_client, session_id, content=b"same content").status_code == 201
    duplicate = _upload(api_client, session_id, content=b"same content")
    assert duplicate.status_code == 409
    assert "already exists" in duplicate.json()["detail"]
    # Same file in another session is allowed.
    assert _upload(api_client, other_session_id, content=b"same content").status_code == 201

    # The rejected duplicate left no file behind (2 accepted uploads, no staging leftovers).
    assert len(list(upload_dir.iterdir())) == 2


def test_upload_rejects_unsupported_extension(api_client):
    response = _upload(api_client, _new_session(api_client), name="malware.exe", content=b"MZ")
    assert response.status_code == 415
    assert PDF_OR_TXT_ONLY in response.json()["detail"]


def test_upload_rejects_missing_extension(api_client):
    response = _upload(api_client, _new_session(api_client), name="README")
    assert response.status_code == 415


def test_upload_rejects_oversized_file_without_leftovers(api_client, monkeypatch, upload_dir):
    monkeypatch.setattr(settings, "MAX_UPLOAD_SIZE_MB", 0)
    response = _upload(api_client, _new_session(api_client), content=b"x")
    assert response.status_code == 413
    assert list(upload_dir.iterdir()) == []


def test_upload_to_unknown_session_is_rejected(api_client, upload_dir):
    response = _upload(api_client, str(uuid.uuid4()))
    assert response.status_code == 400
    assert list(upload_dir.iterdir()) == []


def test_get_download_delete_missing_document(api_client):
    unknown_id = uuid.uuid4()
    assert api_client.get(f"/api/v1/documents/{unknown_id}").status_code == 404
    assert api_client.get(f"/api/v1/documents/{unknown_id}/download").status_code == 404
    assert api_client.delete(f"/api/v1/documents/{unknown_id}").status_code == 404


def test_list_rejects_invalid_pagination(api_client):
    assert api_client.get("/api/v1/documents/?limit=0").status_code == 422
    assert api_client.get("/api/v1/documents/?skip=-1").status_code == 422
