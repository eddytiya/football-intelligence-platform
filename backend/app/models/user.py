from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, UniqueConstraint, false

from app.db.base import Base


class User(Base):
    """Local account for personal favourites and future notifications."""

    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(254), unique=True, nullable=False, index=True)
    password_hash = Column(String(512), nullable=False)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    last_login_at = Column(DateTime, nullable=True)
    is_admin = Column(Boolean, nullable=False, default=False, server_default=false())


class UserFavourite(Base):
    """A signed-in user's followed club or competition."""

    __tablename__ = "user_favourites"
    __table_args__ = (UniqueConstraint("user_id", "entity_type", "entity_id", name="uq_user_favourite"),)

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    entity_type = Column(String(24), nullable=False)
    entity_id = Column(Integer, nullable=False)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)


class UserWatchlist(Base):
    """A fixture watchlist entry. Reminder delivery is intentionally opt-in."""

    __tablename__ = "user_watchlist"
    __table_args__ = (UniqueConstraint("user_id", "match_id", name="uq_user_watchlist_match"),)

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    match_id = Column(Integer, ForeignKey("matches.id"), nullable=False, index=True)
    reminder_minutes = Column(Integer, nullable=False, default=60)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)


class Notification(Base):
    """An in-app notification generated for a watchlisted fixture."""

    __tablename__ = "notifications"
    __table_args__ = (UniqueConstraint("user_id", "match_id", "type", name="uq_notification_user_match_type"),)

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    match_id = Column(Integer, ForeignKey("matches.id"), nullable=True, index=True)
    type = Column(String(32), nullable=False)
    title = Column(String(200), nullable=False)
    body = Column(String(500), nullable=False)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    read_at = Column(DateTime, nullable=True)
