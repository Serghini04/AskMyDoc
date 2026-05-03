from app.services import retrieval


def test_chat_creates_messages_and_returns_answer(api_client, monkeypatch):
    def fake_context(*_args, **_kwargs):
        return "context"

    monkeypatch.setattr(retrieval.RetrievalService, "get_context_for_query", fake_context)

    session_response = api_client.post("/api/v1/sessions/")
    assert session_response.status_code == 201
    session_id = session_response.json()["id"]

    chat_response = api_client.post(
        f"/api/v1/sessions/{session_id}/chat",
        json={"message": "Hello"},
    )

    assert chat_response.status_code == 200
    assert chat_response.json()["content"] == "test-answer"

    session_detail = api_client.get(f"/api/v1/sessions/{session_id}")
    assert session_detail.status_code == 200
    messages = session_detail.json()["messages"]
    assert len(messages) == 2
    assert messages[0]["role"] == "user"
    assert messages[1]["role"] == "assistant"
