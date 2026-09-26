import logging
from abc import ABC, abstractmethod
from collections.abc import Sequence
from functools import lru_cache
from typing import TypedDict

from openai import APIError, OpenAI

from app.config import settings
from app.exceptions import ProviderUnavailableError
from app.services import prompts

logger = logging.getLogger(__name__)

# One retry for "successful" responses that carry no answer (see _complete).
EMPTY_RESPONSE_ATTEMPTS = 2
SDK_MAX_RETRIES = 2


class ChatTurn(TypedDict):
    role: str
    content: str


class LLMUnavailableError(ProviderUnavailableError):
    """The provider couldn't produce an answer (rate limit, outage, bad response)."""


class BaseLLMService(ABC):
    @abstractmethod
    def generate_answer(self, context: str, history: Sequence[ChatTurn], question: str) -> str:
        """Answer `question` grounded in `context`, continuing `history`."""

    @abstractmethod
    def generate_title(self, question: str, answer: str) -> str:
        """Produce a short title summarizing a session's first exchange."""


class OpenAICompatibleLLMService(BaseLLMService):
    """
    Any provider exposing the OpenAI Chat Completions API (OpenAI, OpenRouter,
    Groq, Ollama, ...). Switching provider is a config change:
    LLM_BASE_URL, LLM_API_KEY, LLM_MODEL.
    """

    def __init__(self) -> None:
        self.client = OpenAI(
            base_url=settings.LLM_BASE_URL,
            api_key=settings.LLM_API_KEY.get_secret_value(),
            timeout=settings.LLM_TIMEOUT_SECONDS,
            max_retries=SDK_MAX_RETRIES,
        )
        self.model = settings.LLM_MODEL
        # OpenRouter's `models` parameter routes to the next model on failure.
        fallbacks = settings.llm_fallback_models_list
        self._extra_body = {"models": [self.model, *fallbacks]} if fallbacks else None

    def generate_answer(self, context: str, history: Sequence[ChatTurn], question: str) -> str:
        messages: list[ChatTurn] = [
            {"role": "system", "content": prompts.build_answer_system_prompt(context)},
            *history,
            {"role": "user", "content": question},
        ]
        return self._complete(messages)

    def generate_title(self, question: str, answer: str) -> str:
        return self._complete(
            [
                {"role": "system", "content": prompts.TITLE_SYSTEM_PROMPT},
                {"role": "user", "content": prompts.build_title_user_prompt(question, answer)},
            ]
        )

    def _complete(self, messages: Sequence[ChatTurn]) -> str:
        for attempt in range(1, EMPTY_RESPONSE_ATTEMPTS + 1):
            try:
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=list(messages),  # type: ignore[arg-type]
                    extra_body=self._extra_body,
                )
            except APIError as exc:
                # The SDK already retried 429/5xx/timeouts; give up cleanly.
                raise LLMUnavailableError(str(exc)) from exc

            # OpenRouter can report upstream failures as HTTP 200 with an
            # `error` object and no choices; the SDK doesn't raise on that.
            if response.choices:
                if response.model and response.model != self.model:
                    logger.info("LLM served by fallback model: %s", response.model)
                return response.choices[0].message.content or ""

            logger.warning(
                "LLM returned no choices (attempt %d/%d): %s",
                attempt,
                EMPTY_RESPONSE_ATTEMPTS,
                (response.model_extra or {}).get("error"),
            )

        raise LLMUnavailableError("Provider returned no answer.")


@lru_cache(maxsize=1)
def get_llm_service() -> BaseLLMService:
    return OpenAICompatibleLLMService()
