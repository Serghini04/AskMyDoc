from types import SimpleNamespace

import pytest

from app.services import llm as llm_module
from app.services.llm import LLMUnavailableError, OpenAICompatibleLLMService


def _service_returning(*responses):
    service = OpenAICompatibleLLMService.__new__(OpenAICompatibleLLMService)
    service.model = "primary"
    service._extra_body = None
    calls = iter(responses)
    service.client = SimpleNamespace(
        chat=SimpleNamespace(completions=SimpleNamespace(create=lambda **_kw: next(calls)))
    )
    return service


def _ok(text):
    message = SimpleNamespace(content=text)
    return SimpleNamespace(model="primary", choices=[SimpleNamespace(message=message)])


EMPTY = SimpleNamespace(model=None, choices=None, model_extra={"error": {"code": 429}})


def test_complete_retries_once_on_empty_choices():
    service = _service_returning(EMPTY, _ok("answer"))
    assert service._complete([{"role": "user", "content": "q"}]) == "answer"


def test_complete_raises_unavailable_when_always_empty():
    service = _service_returning(*[EMPTY] * llm_module.EMPTY_RESPONSE_ATTEMPTS)
    with pytest.raises(LLMUnavailableError):
        service._complete([{"role": "user", "content": "q"}])
