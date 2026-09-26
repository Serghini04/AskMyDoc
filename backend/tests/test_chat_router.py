import uuid

from app.api.dependencies import get_embedding_service
from app.services.embeddings import BaseEmbeddingService, EmbeddingUnavailableError
from app.services.llm import BaseLLMService, LLMUnavailableError, get_llm_service


def _ask(api_client, session_id, message):
    return api_client.post(f"/api/v1/sessions/{session_id}/chat", json={"message": message})


def test_chat_saves_both_messages_in_order(api_client):
    session_id = api_client.post("/api/v1/sessions/").json()["id"]

    response = _ask(api_client, session_id, "Hello")
    assert response.status_code == 200
    assert response.json()["role"] == "assistant"
    assert response.json()["content"] == "test-answer"

    _ask(api_client, session_id, "Again")
    messages = api_client.get(f"/api/v1/sessions/{session_id}").json()["messages"]
    assert [(m["role"], m["content"]) for m in messages] == [
        ("user", "Hello"),
        ("assistant", "test-answer"),
        ("user", "Again"),
        ("assistant", "test-answer"),
    ]


def test_first_message_auto_titles_session_but_not_after_rename(api_client):
    session_id = api_client.post("/api/v1/sessions/").json()["id"]

    _ask(api_client, session_id, "Hi")
    assert api_client.get(f"/api/v1/sessions/{session_id}").json()["title"] == "Generated Title"

    # A manual rename must not be clobbered by later messages.
    api_client.patch(f"/api/v1/sessions/{session_id}", json={"title": "My name"})
    _ask(api_client, session_id, "Again")
    assert api_client.get(f"/api/v1/sessions/{session_id}").json()["title"] == "My name"


def test_title_falls_back_to_question_when_title_generation_fails(api_client, llm):
    def broken_title(question, answer):
        raise RuntimeError("title model down")

    llm.generate_title = broken_title
    session_id = api_client.post("/api/v1/sessions/").json()["id"]

    assert _ask(api_client, session_id, "What is the refund amount this year?").status_code == 200
    title = api_client.get(f"/api/v1/sessions/{session_id}").json()["title"]
    assert title == "What is the refund amount this"


def test_chat_on_unknown_session_returns_404(api_client):
    assert _ask(api_client, uuid.uuid4(), "hi").status_code == 404


def test_chat_rejects_blank_message(api_client):
    session_id = api_client.post("/api/v1/sessions/").json()["id"]
    assert _ask(api_client, session_id, "   ").status_code == 422


def test_chat_returns_503_and_saves_nothing_when_llm_unavailable(api_client):
    class FailingLLM(BaseLLMService):
        def generate_answer(self, context, history, question):
            raise LLMUnavailableError("upstream 429")

        def generate_title(self, question, answer):
            return ""

    api_client.app.dependency_overrides[get_llm_service] = FailingLLM
    session_id = api_client.post("/api/v1/sessions/").json()["id"]

    response = _ask(api_client, session_id, "hello")
    assert response.status_code == 503
    assert "busy" in response.json()["detail"]
    assert "429" not in response.json()["detail"]  # provider details stay in the logs
    # Nothing persisted: Retry must not leave a duplicate unanswered question.
    assert api_client.get(f"/api/v1/sessions/{session_id}").json()["messages"] == []


def test_chat_returns_503_when_embeddings_unavailable(api_client):
    class DownEmbeddings(BaseEmbeddingService):
        def embed_texts(self, texts):
            raise EmbeddingUnavailableError("provider down")

    api_client.app.dependency_overrides[get_embedding_service] = DownEmbeddings
    session_id = api_client.post("/api/v1/sessions/").json()["id"]

    assert _ask(api_client, session_id, "hello").status_code == 503
    assert api_client.get(f"/api/v1/sessions/{session_id}").json()["messages"] == []
