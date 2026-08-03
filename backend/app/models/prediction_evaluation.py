from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.db.base import Base


class PredictionEvaluation(Base):
    """
    Stores the evaluation of a prediction after
    the corresponding match has finished.
    """

    __tablename__ = "prediction_evaluations"

    # ==========================================================
    # Primary Key
    # ==========================================================

    id = Column(
        Integer,
        primary_key=True,
        index=True,
    )

    # ==========================================================
    # Foreign Key
    # ==========================================================

    prediction_id = Column(
        Integer,
        ForeignKey(
            "predictions.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        unique=True,
        index=True,
    )

    # ==========================================================
    # Evaluation
    # ==========================================================

    actual_result = Column(
        String(30),
        nullable=False,
    )

    correct = Column(
        Boolean,
        nullable=False,
    )

    evaluated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    # ==========================================================
    # Relationships
    # ==========================================================

    prediction = relationship(
        "Prediction",
        back_populates="evaluation",
    )