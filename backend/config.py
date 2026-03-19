from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    # App
    APP_NAME: str = "CodeSentinel"
    DEBUG: bool = False
    SECRET_KEY: str = "change-me-in-production"

    # Database
    DATABASE_URL: str = "postgresql://sentinel:sentinel@localhost:5432/codesentinel"

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"

    # LLM
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "codellama:13b"

    # GitHub
    GITHUB_TOKEN: Optional[str] = None

    # VirusTotal
    VIRUSTOTAL_API_KEY: Optional[str] = None

    # MITRE ATT&CK
    MITRE_ATTACK_URL: str = "https://raw.githubusercontent.com/mitre/cti/master/enterprise-attack/enterprise-attack.json"

    # Scan limits
    MAX_REPO_SIZE_MB: int = 100
    MAX_FILES_PER_SCAN: int = 500
    SCAN_TIMEOUT_SECONDS: int = 300

    # Sandbox
    SANDBOX_IMAGE: str = "codesentinel-sandbox:latest"
    SANDBOX_TIMEOUT_SECONDS: int = 30

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
