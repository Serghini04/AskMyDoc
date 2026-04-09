import uuid

from app.api.routers import documents


def test_upload_list_get_download_delete_full_flow(api_client, monkeypatch):
    calls: list[dict] = []

    def fake_background(doc_id, file_path, ext):
        calls.append(
            {
                "doc_id": str(doc_id),
                "file_path": file_path,
                "ext": ext,
            }
        )

    monkeypatch.setattr(documents, "process_document_background", fake_background)

    response = api_client.post(
        "/api/v1/documents/",
        files={"file": ("contract.txt", b"hello from test", "text/plain")},
    )
    assert response.status_code == 201

    payload = response.json()
    doc_id = payload["id"]
    assert payload["filename"] == "contract.txt"
    assert payload["status"] == "PENDING"

    assert len(calls) == 1
    assert calls[0]["doc_id"] == doc_id
    assert calls[0]["ext"] == ".txt"

    list_response = api_client.get("/api/v1/documents/")
    assert list_response.status_code == 200
    assert len(list_response.json()) == 1

    get_response = api_client.get(f"/api/v1/documents/{doc_id}")
    assert get_response.status_code == 200
    assert get_response.json()["id"] == doc_id

    download_response = api_client.get(f"/api/v1/documents/{doc_id}/download")
    assert download_response.status_code == 200
    assert download_response.content == b"hello from test"

    delete_response = api_client.delete(f"/api/v1/documents/{doc_id}")
    assert delete_response.status_code == 204

    missing_response = api_client.get(f"/api/v1/documents/{doc_id}")
    assert missing_response.status_code == 404


def test_upload_rejects_duplicate_by_hash(api_client, monkeypatch):
    monkeypatch.setattr(documents, "process_document_background", lambda *args, **kwargs: None)

    file_payload = {"file": ("same.txt", b"same content", "text/plain")}

    first = api_client.post("/api/v1/documents/", files=file_payload)
    assert first.status_code == 201

    second = api_client.post("/api/v1/documents/", files=file_payload)
    assert second.status_code == 409


def test_upload_rejects_unsupported_extension(api_client):
    response = api_client.post(
        "/api/v1/documents/",
        files={"file": ("malware.exe", b"MZ", "application/octet-stream")},
    )
    assert response.status_code == 415


def test_get_download_delete_missing_document(api_client):
    unknown_id = str(uuid.uuid4())

    assert api_client.get(f"/api/v1/documents/{unknown_id}").status_code == 404
    assert api_client.get(f"/api/v1/documents/{unknown_id}/download").status_code == 404
    assert api_client.delete(f"/api/v1/documents/{unknown_id}").status_code == 404
