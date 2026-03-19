from pydantic_settings import BaseSettings
from pydantic import ConfigDict
from typing import Optional


class Settings(BaseSettings):
    model_config = ConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,   # allows GROQ_API_KEY or groq_api_key
        extra="ignore",         # ignore any unknown env vars — critical fix
    )

    # App
    APP_NAME: str = "CodeSentinel"
    DEBUG: bool = False
    SECRET_KEY: str = "change-me-in-production"

    # Database
    DATABASE_URL: str = "sqlite+aiosqlite:///./codesentinel.db"

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"

    # Groq LLM (free at console.groq.com)
    GROQ_API_KEY: Optional[str] = None
    GROQ_MODEL: str = "llama3-8b-8192"

    # GitHub
    GITHUB_TOKEN: Optional[str] = None

    # VirusTotal (optional)
    VIRUSTOTAL_API_KEY: Optional[str] = None

    # Scan limits
    MAX_REPO_SIZE_MB: int = 100
    MAX_FILES_PER_SCAN: int = 500
    SCAN_TIMEOUT_SECONDS: int = 300
    SANDBOX_TIMEOUT_SECONDS: int = 30


settings = Settings()