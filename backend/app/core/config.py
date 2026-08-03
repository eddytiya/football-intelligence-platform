from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


BACKEND_ROOT = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    """
    Application settings loaded from the .env file.
    """

    # ==============================
    # DATABASE CONFIGURATION
    # ==============================

    DB_HOST: str
    DB_PORT: int
    DB_NAME: str
    DB_USER: str
    DB_PASSWORD: str

    # ==============================
    # FOOTBALL-DATA API
    # ==============================

    FOOTBALL_API_KEY: str
    FOOTBALL_API_BASE_URL: str

    # API-Football is used only for richer squad/player coverage. Keeping its
    # credentials separate avoids mixing provider identifiers.
    API_FOOTBALL_KEY: str | None = None
    API_FOOTBALL_BASE_URL: str = "https://v3.football.api-sports.io"
    # Squad imports run as a small rotating batch. The job only covers the
    # competitions selected for this product and stays beneath the free-tier
    # allowance by refreshing at most 30 clubs in a 26-hour window.
    API_FOOTBALL_SQUAD_SYNC_ENABLED: bool = False
    API_FOOTBALL_SQUAD_SYNC_DAILY_LIMIT: int = 30
    API_FOOTBALL_SQUAD_SYNC_INTERVAL_HOURS: int = 26

    # ==============================
    # HTTP CLIENT
    # ==============================

    REQUEST_TIMEOUT: int
    MAX_RETRIES: int
    RETRY_DELAY: int

    # ==============================
    # APPLICATION
    # ==============================

    ENVIRONMENT: str
    DEBUG: bool

    # Local-account access tokens are signed with this server-only value.
    AUTH_SECRET_KEY: str = "replace-this-development-secret-before-deployment"
    AUTH_TOKEN_EXPIRE_HOURS: int = 168

    # Comma-separated browser origins allowed to call the API. Add the
    # deployed Vite URL here when hosting; keep localhost for development.
    CORS_ORIGINS: str = "http://localhost:5173"

    # ==============================
    # LIVE SCORE REFRESH
    # ==============================

    # The provider is polled sparingly to remain within the football-data.org
    # free-tier request limit. Set this false to disable automatic syncing.
    LIVE_SCORE_SYNC_ENABLED: bool = True
    LIVE_SCORE_SYNC_INTERVAL_MINUTES: int = 10
    FUTURE_FIXTURE_SYNC_DAYS: int = 90
    FUTURE_FIXTURE_SYNC_INTERVAL_HOURS: int = 24

    # ==============================
    # WATCHLIST NOTIFICATIONS
    # ==============================

    # In-app notifications work immediately with no configuration. Email
    # delivery stays off until both a provider is configured and this flag is
    # turned on, so nothing attempts to send until you're ready.
    WATCHLIST_NOTIFICATION_INTERVAL_MINUTES: int = 5
    NOTIFICATIONS_EMAIL_ENABLED: bool = False
    SMTP_HOST: str | None = None
    SMTP_PORT: int = 587
    SMTP_USERNAME: str | None = None
    SMTP_PASSWORD: str | None = None
    SMTP_FROM_EMAIL: str | None = None

    # ==============================
    # NEWS
    # ==============================

    # Optional real-headline feed (e.g. https://newsapi.org). Unset by
    # default; the /news endpoint reports itself as not configured until a
    # key is added, rather than failing.
    NEWS_API_KEY: str | None = None
    NEWS_API_BASE_URL: str = "https://newsapi.org/v2"

    model_config = SettingsConfigDict(
        # Resolve relative to the backend package, rather than the shell's
        # working directory. This makes `uvicorn app.main:app` and pytest
        # behave the same whether they are launched from the repository root
        # or from backend/.
        env_file=BACKEND_ROOT / ".env",
        env_file_encoding="utf-8",
    )


settings = Settings()
