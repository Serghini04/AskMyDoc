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


def test_first_message_auto_titles_session(api_client, monkeypatch):
    monkeypatch.setattr(
        retrieval.RetrievalService, "get_context_for_query", lambda *_a, **_kw: "ctx"
    )

    session_id = api_client.post("/api/v1/sessions/").json()["id"]

    # First message → title generated from the exchange.
    api_client.post(f"/api/v1/sessions/{session_id}/chat", json={"message": "Hi"})
    assert api_client.get(f"/api/v1/sessions/{session_id}").json()["title"] == "Generated Title"

    # A manual rename must not be clobbered by later messages.
    api_client.patch(f"/api/v1/sessions/{session_id}", json={"title": "My name"})
    api_client.post(f"/api/v1/sessions/{session_id}/chat", json={"message": "Again"})
    assert api_client.get(f"/api/v1/sessions/{session_id}").json()["title"] == "My name"


def test_chat_returns_503_when_llm_unavailable(api_client, monkeypatch):
    from app.services.llm import LLMUnavailableError, get_llm_service

    monkeypatch.setattr(
        retrieval.RetrievalService, "get_context_for_query", lambda *_a, **_kw: "ctx"
    )

    class FailingLLM:
        def generate_answer(self, **_kwargs):
            raise LLMUnavailableError("upstream 429")

        def generate_title(self, *_args):
            return ""

    api_client.app.dependency_overrides[get_llm_service] = lambda: FailingLLM()
    session_id = api_client.post("/api/v1/sessions/").json()["id"]

    response = api_client.post(
        f"/api/v1/sessions/{session_id}/chat", json={"message": "hello"}
    )

    assert response.status_code == 503
    assert "busy" in response.json()["detail"]
    # Nothing persisted: Retry must not leave a duplicate unanswered question.
    assert api_client.get(f"/api/v1/sessions/{session_id}").json()["messages"] == []
