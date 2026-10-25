"""Provision the administrator configured in server env or the private root .env.access."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from dotenv import dotenv_values
from sqlalchemy import inspect, text
from app.core.config import settings
from app.db.database import engine
from app.db.session import SessionLocal
from app.models.forecast_snapshot import ForecastSnapshot
from app.models.user import User
from app.services.admin_account import ensure_admin_account


def main():
    access = dotenv_values(Path(__file__).resolve().parents[2] / ".env.access")
    email = settings.ADMIN_EMAIL or access.get("ADMIN_EMAIL")
    password = settings.ADMIN_PASSWORD or access.get("ADMIN_PASSWORD")
    if not email or not password:
        raise SystemExit("Set ADMIN_EMAIL and ADMIN_PASSWORD in server env or .env.access first.")
    engine.echo = False
    User.__table__.create(engine, checkfirst=True)
    if "is_admin" not in {column["name"] for column in inspect(engine).get_columns("users")}:
        with engine.begin() as connection:
            connection.execute(text("ALTER TABLE users ADD COLUMN is_admin BOOLEAN NOT NULL DEFAULT FALSE"))
    ForecastSnapshot.__table__.create(engine, checkfirst=True)
    with SessionLocal() as db:
        ensure_admin_account(db, email, password)
    print("Configured administrator is ready; password was not displayed.")


if __name__ == "__main__":
    main()
