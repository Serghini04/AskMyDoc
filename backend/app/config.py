from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import SecretStr


class Settings(BaseSettings):
    # Database
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_DB: str
    POSTGRES_HOST: str
    POSTGRES_PORT: int
    DATABASE_URL: str

    # Vector DB
    QDRANT_HOST: str
    QDRANT_PORT: int
    QDRANT_URL: str

    # LLM — any OpenAI-compatible endpoint (default: OpenRouter)
    LLM_BASE_URL: str = "https://openrouter.ai/api/v1"
    LLM_API_KEY: SecretStr
    LLM_MODEL: str = "google/gemma-4-26b-a4b-it:free"
    # OpenRouter-only: comma-separated models tried in order if LLM_MODEL fails
    # (e.g. free-tier 429s). Leave empty for other providers.
    LLM_FALLBACK_MODELS: str = ""
    LLM_TIMEOUT_SECONDS: float = 60.0

    @property
    def llm_fallback_models_list(self) -> list[str]:
        return [m.strip() for m in self.LLM_FALLBACK_MODELS.split(",") if m.strip()]

    # Embeddings — fastembed local ONNX model, no API key required
    # BAAI/bge-small-en-v1.5 → 384 dims
    # BAAI/bge-base-en-v1.5  → 768 dims
    FASTEMBED_MODEL: str = "BAAI/bge-small-en-v1.5"
    EMBEDDING_DIMENSIONS: int = 384

    # Upload
    MAX_UPLOAD_SIZE_MB: int = 50

    # CORS — comma-separated list of allowed frontend origins
    CORS_ORIGINS: str = "http://localhost:3000"

    @property
    def cors_origins_list(self) -> list[str]:
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()]

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()
