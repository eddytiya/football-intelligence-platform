from sqlalchemy import text

from app.db.session import SessionLocal


session = SessionLocal()

try:
    result = session.execute(text("SELECT current_database();"))

    print("Connected Database:", result.scalar())

finally:
    session.close()