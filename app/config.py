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

    # LLM — GitHub Models (Azure OpenAI-compatible endpoint)
    GITHUB_TOKEN: SecretStr
    GITHUB_MODEL: str = "o4-mini"

    # Embeddings — fastembed local ONNX model, no API key required
    # BAAI/bge-small-en-v1.5 → 384 dims
    # BAAI/bge-base-en-v1.5  → 768 dims
    FASTEMBED_MODEL: str = "BAAI/bge-small-en-v1.5"
    EMBEDDING_DIMENSIONS: int = 384

    # Upload
    MAX_UPLOAD_SIZE_MB: int = 50

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()
