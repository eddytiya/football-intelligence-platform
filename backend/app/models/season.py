from sqlalchemy import Column, Integer, String, Date, ForeignKey
from sqlalchemy.orm import relationship

from app.db.base import Base


class Season(Base):
    __tablename__ = "seasons"

    # ==========================================================
    # Primary Key
    # ==========================================================

    id = Column(
        Integer,
        primary_key=True,
        index=True,
    )

    # ==========================================================
    # External Provider Season ID
    # ==========================================================

    # Football-Data.org provides this.
    # Historical CSV datasets do not, so it is nullable.
    api_id = Column(
        Integer,
        unique=True,
        nullable=True,
    )

    # ==========================================================
    # Competition
    # ==========================================================

    competition_id = Column(
        Integer,
        ForeignKey("competitions.id"),
        nullable=False,
    )

    # ==========================================================
    # Season Information
    # ==========================================================

    # Example: "2025/26"
    season_name = Column(
        String,
        nullable=False,
    )

    # Example: 2025
    start_year = Column(
        Integer,
        nullable=False,
    )

    # Example: 2026
    end_year = Column(
        Integer,
        nullable=False,
    )

    # Football-Data.org only
    start_date = Column(
        Date,
        nullable=True,
    )

    end_date = Column(
        Date,
        nullable=True,
    )

    current_matchday = Column(
        Integer,
        nullable=True,
    )

    # ==========================================================
    # Winner
    # ==========================================================

    winner_team_id = Column(
        Integer,
        ForeignKey("teams.id"),
        nullable=True,
    )

    # ==========================================================
    # Relationships
    # ==========================================================

    competition = relationship(
        "Competition",
        back_populates="seasons",
    )

    winner = relationship(
        "Team",
        foreign_keys=[winner_team_id],
        back_populates="won_seasons",
    )

    matches = relationship(
        "Match",
        back_populates="season",
        cascade="all, delete-orphan",
    )

    standings = relationship(
        "Standing",
        back_populates="season",
        cascade="all, delete-orphan",
    )

    def __repr__(self):
        return (
            f"<Season("
            f"{self.season_name}"
            f")>"
        )