"""Server-recorded forecasts, kept separate from retrospective reviews."""
from datetime import datetime, timezone
from sqlalchemy import Column, DateTime, ForeignKey, Integer, JSON, String, UniqueConstraint
from app.db.base import Base


class ForecastSnapshot(Base):
    __tablename__ = 'forecast_snapshots'
    __table_args__ = (UniqueConstraint('match_id', 'model_version', 'kind', name='uq_forecast_snapshot'),)
    id = Column(Integer, primary_key=True)
    match_id = Column(Integer, ForeignKey('matches.id'), nullable=False, index=True)
    model_version = Column(String(200), nullable=False)
    kind = Column(String(24), nullable=False)
    generated_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    kickoff_at = Column(DateTime(timezone=True), nullable=False)
    payload = Column(JSON, nullable=False)
