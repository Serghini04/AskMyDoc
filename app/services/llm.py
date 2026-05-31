import logging
from abc import ABC, abstractmethod
from functools import lru_cache
from typing import List, Dict

from openai import OpenAI

from app.config import settings


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


class GitHubModelsService(BaseLLMService):
    def __init__(self):
        token = settings.GITHUB_TOKEN.get_secret_value() if settings.GITHUB_TOKEN else None
        if not token:
            logging.warning("GITHUB_TOKEN is missing.")
        self.client = OpenAI(
            base_url="https://models.inference.ai.azure.com",
            api_key=token,
        )
        self.model = settings.GITHUB_MODEL

    def generate_answer(
        self,
        system_prompt: str,
        context: str,
        history: List[Dict[str, str]],
        question: str,
    ) -> str:
        full_system = f"{system_prompt}\n\nCONTEXT FROM DOCUMENTS:\n{context}"

        messages = [{"role": "system", "content": full_system}]
        for msg in history:
            messages.append({"role": msg["role"], "content": msg["content"]})
        messages.append({"role": "user", "content": question})

        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
        )
        return response.choices[0].message.content or ""


@lru_cache(maxsize=1)
def get_llm_service() -> BaseLLMService:
    return GitHubModelsService()
