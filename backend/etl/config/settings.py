from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


BACKEND_ROOT = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    """
    Application configuration loaded from the .env file.
    """

    # ==========================
    # Database
    # ==========================

    DB_HOST: str
    DB_PORT: int
    DB_NAME: str
    DB_USER: str
    DB_PASSWORD: str
    # Managed Postgres providers (e.g. Neon, Supabase) require "require";
    # leave blank for a local database with no TLS.
    DB_SSLMODE: str = ""

    # ==========================
    # Football Data API
    # ==========================

    FOOTBALL_API_KEY: str = ""
    FOOTBALL_API_BASE_URL: str

    # ==========================
    # HTTP Client
    # ==========================

    REQUEST_TIMEOUT: int
    MAX_RETRIES: int
    RETRY_DELAY: int

    # ==========================
    # Environment
    # ==========================

    ENVIRONMENT: str
    DEBUG: bool

    model_config = SettingsConfigDict(
        env_file=BACKEND_ROOT / ".env",
        env_file_encoding="utf-8",
        # This legacy database configuration is intentionally limited to its
        # own settings; other providers may add keys to the shared .env file.
        extra="ignore",
    )


settings = Settings()
