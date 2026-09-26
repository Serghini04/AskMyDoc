import logging
import re
from abc import ABC, abstractmethod
from collections.abc import Sequence
from concurrent.futures import ThreadPoolExecutor
from functools import lru_cache

from openai import APIError, BadRequestError, OpenAI

from app.config import settings
from app.exceptions import ProviderUnavailableError

logger = logging.getLogger(__name__)

Vector = list[float]

# One retry for "successful" responses that carry no/partial data.
EMPTY_RESPONSE_ATTEMPTS = 2
SDK_MAX_RETRIES = 3

# Providers reject (rather than truncate) inputs over the model's token limit,
# e.g. "Embedding input has 616 tokens, exceeding the model maximum of 512."
TOKEN_LIMIT_PATTERN = re.compile(r"has (\d+) tokens, exceeding the model maximum of (\d+)")
MAX_SHORTEN_ATTEMPTS = 3


class _InputTooLongError(Exception):
    def __init__(self, tokens: int, limit: int):
        super().__init__(f"{tokens} tokens > {limit}")
        self.tokens = tokens
        self.limit = limit


class EmbeddingUnavailableError(ProviderUnavailableError):
    """The embedding provider couldn't return valid vectors."""


class BaseEmbeddingService(ABC):
    @abstractmethod
    def embed_texts(self, texts: Sequence[str]) -> list[Vector]:
        """Embed many texts; returns one vector per input, in input order."""

    def embed_text(self, text: str) -> Vector:
        return self.embed_texts([text])[0]


class OpenAICompatibleEmbeddingService(BaseEmbeddingService):
    """
    Embeddings from any OpenAI-compatible /embeddings endpoint (OpenAI by
    default). Switching model is a config change — but vectors from different
    models aren't comparable, so it requires `make reindex`.
    """

    def __init__(self) -> None:
        self.client = OpenAI(
            base_url=settings.EMBEDDING_BASE_URL,
            api_key=settings.embedding_api_key,
            timeout=settings.EMBEDDING_TIMEOUT_SECONDS,
            max_retries=SDK_MAX_RETRIES,
        )
        self.model = settings.EMBEDDING_MODEL
        self.dimensions = settings.EMBEDDING_DIMENSIONS
        self.batch_size = settings.EMBEDDING_BATCH_SIZE
        self.concurrency = settings.EMBEDDING_CONCURRENCY

    def embed_texts(self, texts: Sequence[str]) -> list[Vector]:
        batches = [
            texts[start : start + self.batch_size]
            for start in range(0, len(texts), self.batch_size)
        ]
        if len(batches) <= 1 or self.concurrency <= 1:
            results = [self._embed_batch(batch) for batch in batches]
        else:
            # Throughput is bound by tokens/sec per request, so a large document
            # is much faster with a few batches in flight. map() keeps order.
            with ThreadPoolExecutor(max_workers=self.concurrency) as pool:
                results = list(pool.map(self._embed_batch, batches))
        return [vector for batch_vectors in results for vector in batch_vectors]

    def _embed_batch(self, batch: Sequence[str]) -> list[Vector]:
        try:
            return self._request(batch)
        except _InputTooLongError:
            # The error doesn't say which input was too long: embed one by one.
            return [self._embed_single(text) for text in batch]

    def _embed_single(self, text: str) -> Vector:
        """
        Embed one text, shortening it if the provider rejects its length. Only
        the embedding input is shortened — the stored chunk keeps its full
        text. Normal prose never gets here; token-dense text (IDs, barcodes)
        can exceed the limit even at our 1000-char chunk size.
        """
        for _ in range(MAX_SHORTEN_ATTEMPTS + 1):
            try:
                return self._request([text])[0]
            except _InputTooLongError as exc:
                new_length = int(len(text) * exc.limit / exc.tokens * 0.9)
                logger.warning(
                    "Embedding input too long (%d tokens > %d); shortening %d -> %d chars.",
                    exc.tokens,
                    exc.limit,
                    len(text),
                    new_length,
                )
                text = text[:new_length]
        raise EmbeddingUnavailableError("Input still exceeds the model's token limit.")

    def _request(self, batch: Sequence[str]) -> list[Vector]:
        for attempt in range(1, EMPTY_RESPONSE_ATTEMPTS + 1):
            try:
                response = self.client.embeddings.create(
                    model=self.model,
                    input=batch,
                    # The SDK defaults to base64, which not every provider supports.
                    encoding_format="float",
                )
            except BadRequestError as exc:
                match = TOKEN_LIMIT_PATTERN.search(str(exc))
                if match:
                    raise _InputTooLongError(int(match.group(1)), int(match.group(2))) from exc
                raise EmbeddingUnavailableError(str(exc)) from exc
            except APIError as exc:
                # The SDK already retried 429/5xx/timeouts; give up cleanly.
                raise EmbeddingUnavailableError(str(exc)) from exc

            data = sorted(response.data or [], key=lambda d: d.index)
            if len(data) == len(batch):
                vectors = [d.embedding for d in data]
                if any(len(v) != self.dimensions for v in vectors):
                    # Config error, not a transient one — retrying won't help.
                    raise EmbeddingUnavailableError(
                        f"{self.model} returned {len(vectors[0])}-dim vectors but "
                        f"EMBEDDING_DIMENSIONS={self.dimensions}."
                    )
                return vectors

            logger.warning(
                "Embedding returned %d/%d vectors (attempt %d/%d): %s",
                len(data),
                len(batch),
                attempt,
                EMPTY_RESPONSE_ATTEMPTS,
                (response.model_extra or {}).get("error"),
            )

        raise EmbeddingUnavailableError("Provider returned incomplete embeddings.")


@lru_cache(maxsize=1)
def get_embedding_service() -> BaseEmbeddingService:
    return OpenAICompatibleEmbeddingService()
