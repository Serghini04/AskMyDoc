import logging
from abc import ABC, abstractmethod
from functools import lru_cache
from typing import List, Dict

from openai import APIError, OpenAI

from app.config import settings


# One retry for "successful" responses that carry no answer (see _complete).
EMPTY_RESPONSE_ATTEMPTS = 2


class LLMUnavailableError(Exception):
    """The provider couldn't produce an answer (rate limit, outage, bad response)."""


class BaseLLMService(ABC):
    @abstractmethod
    def generate_answer(
        self,
        system_prompt: str,
        context: str,
        history: List[Dict[str, str]],
        question: str,
    ) -> str:
        pass

    @abstractmethod
    def generate_title(self, question: str, answer: str) -> str:
        """Produce a short title summarizing a session's first exchange."""
        pass


class OpenAICompatibleLLMService(BaseLLMService):
    """
    Talks to any provider exposing the OpenAI Chat Completions API
    (OpenRouter, OpenAI, Groq, GitHub Models, Ollama...). Switching provider
    is a config change: LLM_BASE_URL, LLM_API_KEY, LLM_MODEL.
    """

    def __init__(self):
        token = settings.LLM_API_KEY.get_secret_value() if settings.LLM_API_KEY else None
        if not token:
            logging.warning("LLM_API_KEY is missing.")
        self.client = OpenAI(
            base_url=settings.LLM_BASE_URL,
            api_key=token,
            timeout=settings.LLM_TIMEOUT_SECONDS,
            max_retries=2,
        )
        self.model = settings.LLM_MODEL
        # OpenRouter's `models` param routes to the next model on failure.
        fallbacks = settings.llm_fallback_models_list
        self._extra_body = {"models": [self.model, *fallbacks]} if fallbacks else None

    def _complete(self, messages: List[Dict[str, str]]) -> str:
        for attempt in range(1, EMPTY_RESPONSE_ATTEMPTS + 1):
            try:
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    extra_body=self._extra_body,
                )
            except APIError as exc:
                # The SDK already retried 429/5xx/timeouts; give up cleanly.
                raise LLMUnavailableError(str(exc)) from exc

            # OpenRouter can report upstream failures as HTTP 200 with an
            # `error` object and no choices; the SDK doesn't raise on that.
            if response.choices:
                if response.model and response.model != self.model:
                    logging.info("LLM served by fallback model: %s", response.model)
                return response.choices[0].message.content or ""

            logging.warning(
                "LLM returned no choices (attempt %d/%d): %s",
                attempt,
                EMPTY_RESPONSE_ATTEMPTS,
                (response.model_extra or {}).get("error"),
            )

        raise LLMUnavailableError("Provider returned no answer.")

    def generate_answer(
        self,
        system_prompt: str,
        context: str,
        history: List[Dict[str, str]],
        question: str,
    ) -> str:
        # Say "nothing found" as an instruction, not as document text the
        # model might quote back as if the user's file said it.
        context_block = context or (
            "(No passages from this chat's documents matched the question, "
            "or no documents have been added yet.)"
        )
        full_system = f"{system_prompt}\n\nCONTEXT FROM DOCUMENTS:\n{context_block}"

        messages = [{"role": "system", "content": full_system}]
        for msg in history:
            messages.append({"role": msg["role"], "content": msg["content"]})
        messages.append({"role": "user", "content": question})

        return self._complete(messages)

    def generate_title(self, question: str, answer: str) -> str:
        system_prompt = (
            "You name chat conversations. Given the first exchange, reply with a "
            "concise title of 3 to 6 words that captures the topic. Respond with "
            "ONLY the title — no quotes, no trailing punctuation, no 'Title:' prefix."
        )
        messages = [
            {"role": "system", "content": system_prompt},
            {
                "role": "user",
                "content": f"User question:\n{question}\n\nAssistant answer:\n{answer}",
            },
        ]
        return self._complete(messages)


@lru_cache(maxsize=1)
def get_llm_service() -> BaseLLMService:
    return OpenAICompatibleLLMService()
