"""Application configuration via Pydantic Settings."""

from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """All application settings, read from environment variables."""

    # Database
    DATABASE_URL: str = "postgresql+asyncpg://sbom:sbom_password@localhost:5432/sbom_risk_scorer"
    SYNC_DATABASE_URL: str = "postgresql://sbom:sbom_password@localhost:5432/sbom_risk_scorer"

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"

    # Celery
    CELERY_BROKER_URL: str = "redis://localhost:6379/1"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/1"

    # GitHub API
    GITHUB_TOKEN: str = ""

    # Anthropic Claude API
    ANTHROPIC_API_KEY: str = ""

    # File storage
    SBOM_STORAGE_PATH: str = "./storage/sboms"

    # App
    API_V1_PREFIX: str = "/api/v1"
    DEBUG: bool = True
    MAX_SBOM_SIZE_BYTES: int = 20 * 1024 * 1024  # 20 MB

    # Cache TTLs (seconds)
    OSV_CACHE_TTL: int = 86400  # 24 hours
    GITHUB_CACHE_TTL: int = 21600  # 6 hours

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


@lru_cache()
def get_settings() -> Settings:
    """Cached settings instance."""
    return Settings()
