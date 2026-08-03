from sqlalchemy import create_engine

from etl.config.settings import settings


DATABASE_URL = (
    f"postgresql+psycopg2://"
    f"{settings.DB_USER}:"
    f"{settings.DB_PASSWORD}@"
    f"{settings.DB_HOST}:"
    f"{settings.DB_PORT}/"
    f"{settings.DB_NAME}"
    + (f"?sslmode={settings.DB_SSLMODE}" if settings.DB_SSLMODE else "")
)

engine = create_engine(
    DATABASE_URL,
    echo=settings.DEBUG,
)