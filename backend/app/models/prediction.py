from sqlalchemy import (
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.db.base import Base


class Prediction(Base):
    """
    Stores machine learning predictions for football matches.
    """

    __tablename__ = "predictions"

    # ==========================================================
    # Primary Key
    # ==========================================================

    id = Column(
        Integer,
        primary_key=True,
        index=True,
    )

    # ==========================================================
    # Foreign Keys
    # ==========================================================

    match_id = Column(
        Integer,
        ForeignKey("matches.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # ==========================================================
    # Prediction Information
    # ==========================================================

    model_name = Column(
        String(100),
        nullable=False,
    )

    prediction = Column(
        String(30),
        nullable=False,
    )

    home_probability = Column(
        Float,
        nullable=False,
    )

    draw_probability = Column(
        Float,
        nullable=False,
    )

    away_probability = Column(
        Float,
        nullable=False,
    )

    predicted_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    # ==========================================================
    # Relationships
    # ==========================================================

    match = relationship(
        "Match",
        back_populates="predictions",
    )

    evaluation = relationship(
        "PredictionEvaluation",
        back_populates="prediction",
        uselist=False,
        cascade="all, delete-orphan",
    )