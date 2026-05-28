from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import SecretStr, model_validator

class Settings(BaseSettings):
    # Database Config
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_DB: str
    POSTGRES_HOST: str
    POSTGRES_PORT: int
    DATABASE_URL: str

    # Vector DB Config
    QDRANT_HOST: str
    QDRANT_PORT: int
    QDRANT_URL: str

    # AI Config
    LLM_PROVIDER: str = "gemini"
    OPENAI_API_KEY: SecretStr | None = None
    GEMINI_API_KEY: SecretStr | None = None

    @model_validator(mode="after")
    def validate_llm_keys(self) -> "Settings":
        provider = (self.LLM_PROVIDER or "gemini").lower()
        if provider == "gemini" and not self.GEMINI_API_KEY:
            raise ValueError("GEMINI_API_KEY is required when LLM_PROVIDER=gemini")
        if provider == "openai" and not self.OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY is required when LLM_PROVIDER=openai")
        return self

    # Instruct Pydantic to read from the .env file in the root directory
    model_config = SettingsConfigDict(
        env_file=".env", 
        env_file_encoding="utf-8", 
        extra="ignore"
    )

settings = Settings()