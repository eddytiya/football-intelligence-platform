from datetime import datetime
from sqlalchemy import Column, DateTime, ForeignKey, Integer, JSON, String, UniqueConstraint
from app.db.base import Base


class FanPick(Base):
    """Immutable account pick and model snapshot, accepted before verified kickoff."""
    __tablename__ = "fan_picks"
    __table_args__ = (UniqueConstraint("user_id", "match_id", name="uq_fan_pick_user_match"),)
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    match_id = Column(Integer, ForeignKey("matches.id"), nullable=False, index=True)
    outcome = Column(String(8), nullable=False)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    kickoff_at_capture = Column(DateTime, nullable=False)
    home_team_id = Column(Integer, nullable=False)
    away_team_id = Column(Integer, nullable=False)
    model_probabilities = Column(JSON, nullable=True)
    model_version = Column(String(200), nullable=True)
