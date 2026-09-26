from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings, read from environment variables and `.env`."""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    LOG_LEVEL: str = "INFO"

    # Infrastructure
    DATABASE_URL: str
    QDRANT_URL: str
    QDRANT_COLLECTION: str = "document_chunks"

    # LLM — any OpenAI-compatible endpoint (default: OpenAI)
    LLM_BASE_URL: str = "https://api.openai.com/v1"
    LLM_API_KEY: SecretStr
    LLM_MODEL: str = "gpt-4.1-nano"
    # OpenRouter only: comma-separated models tried in order if LLM_MODEL fails.
    LLM_FALLBACK_MODELS: str = ""
    LLM_TIMEOUT_SECONDS: float = 60.0

    # Embeddings — any OpenAI-compatible /embeddings endpoint (default: OpenAI).
    # Changing the model or dimensions requires `make reindex`.
    EMBEDDING_BASE_URL: str = "https://api.openai.com/v1"
    EMBEDDING_API_KEY: SecretStr | None = None  # falls back to LLM_API_KEY
    EMBEDDING_MODEL: str = "text-embedding-3-small"
    EMBEDDING_DIMENSIONS: int = 1536
    # Texts per request; OpenAI allows 2048 inputs / 300k tokens per request.
    EMBEDDING_BATCH_SIZE: int = 128
    # Batches in flight at once for large documents (mind provider rate limits).
    EMBEDDING_CONCURRENCY: int = 4
    EMBEDDING_TIMEOUT_SECONDS: float = 60.0

    # RAG tuning
    CHUNK_SIZE_CHARS: int = 1000
    CHUNK_OVERLAP_CHARS: int = 200  # keeps sentences cut at a boundary whole in a neighbor
    RETRIEVAL_TOP_K: int = 5
    CHAT_HISTORY_MESSAGES: int = 5

    # Uploads
    UPLOAD_DIR: str = "uploads"
    MAX_UPLOAD_SIZE_MB: int = 50

    # CORS — comma-separated list of allowed frontend origins
    CORS_ORIGINS: str = "http://localhost:3000"

    @property
    def llm_fallback_models_list(self) -> list[str]:
        return [m.strip() for m in self.LLM_FALLBACK_MODELS.split(",") if m.strip()]

    @property
    def embedding_api_key(self) -> str | None:
        key = self.EMBEDDING_API_KEY or self.LLM_API_KEY
        return key.get_secret_value() if key else None

    @property
    def max_upload_bytes(self) -> int:
        return self.MAX_UPLOAD_SIZE_MB * 1024 * 1024

    @property
    def cors_origins_list(self) -> list[str]:
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()]


settings = Settings()
