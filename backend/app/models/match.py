from sqlalchemy import (
    Column,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Time,
)
from sqlalchemy.orm import relationship
from sqlalchemy import event

from app.db.base import Base
from app.services.matching.result_validation import validate_match_record


def _validate_match_insert(mapper, connection, target):
    validate_match_record(target)


def _validate_match_update(mapper, connection, target):
    validate_match_record(target, legacy_update=True)


class Match(Base):
    """
    Stores football matches from multiple providers.

    Supported Sources
    -----------------
    - Football-Data.org
    - football-data.co.uk
    - StatsBomb (future)
    - Opta (future)
    - Other providers (future)
    """

    __tablename__ = "matches"

    # ==========================================================
    # Primary Key
    # ==========================================================

    id = Column(
        Integer,
        primary_key=True,
        index=True,
    )

    # ==========================================================
    # External Provider Match ID
    # ==========================================================

    # Football-Data.org:
    #     "498238"
    #
    # Historical CSV:
    #     "PL_2025_Arsenal_Chelsea_2025-02-15"
    #
    # Store as String so every provider is supported.
    api_id = Column(
        String(255),
        unique=True,
        nullable=False,
        index=True,
    )

    # ==========================================================
    # Foreign Keys
    # ==========================================================

    competition_id = Column(
        Integer,
        ForeignKey("competitions.id"),
        nullable=False,
    )

    season_id = Column(
        Integer,
        ForeignKey("seasons.id"),
        nullable=True,
    )

    referee_id = Column(
        Integer,
        ForeignKey("referees.id"),
        nullable=True,
    )

    stadium_id = Column(
        Integer,
        ForeignKey("stadiums.id"),
        nullable=True,
    )

    home_team_id = Column(
        Integer,
        ForeignKey("teams.id"),
        nullable=False,
    )

    away_team_id = Column(
        Integer,
        ForeignKey("teams.id"),
        nullable=False,
    )

    # ==========================================================
    # Match Information
    # ==========================================================

    utc_date = Column(
        DateTime,
        nullable=True,
    )

    match_date = Column(
        Date,
        nullable=True,
    )

    kick_off = Column(
        Time,
        nullable=True,
    )

    status = Column(
        String(50),
        nullable=True,
    )

    match_week = Column(
        Integer,
        nullable=True,
    )

    stage = Column(
        String(100),
        nullable=True,
    )

    # ==========================================================
    # Final Score
    # ==========================================================

    home_score = Column(
        Integer,
        default=0,
    )

    away_score = Column(
        Integer,
        default=0,
    )

    # ==========================================================
    # Relationships
    # ==========================================================

    competition = relationship(
        "Competition",
        back_populates="matches",
    )

    season = relationship(
        "Season",
        back_populates="matches",
    )

    referee = relationship(
        "Referee",
        back_populates="matches",
    )

    stadium = relationship(
        "Stadium",
        back_populates="matches",
    )

    home_team = relationship(
        "Team",
        foreign_keys=[home_team_id],
        back_populates="home_matches",
    )

    away_team = relationship(
        "Team",
        foreign_keys=[away_team_id],
        back_populates="away_matches",
    )

    # ==========================================================
    # Match Details
    # ==========================================================

    events = relationship(
        "MatchEvent",
        back_populates="match",
        cascade="all, delete-orphan",
    )

    lineups = relationship(
        "Lineup",
        back_populates="match",
        cascade="all, delete-orphan",
    )

    officials = relationship(
        "MatchOfficial",
        back_populates="match",
        cascade="all, delete-orphan",
    )

    # ==========================================================
    # Statistics
    # ==========================================================

    team_statistics = relationship(
        "TeamStatistics",
        back_populates="match",
        cascade="all, delete-orphan",
    )

    player_statistics = relationship(
        "PlayerStatistics",
        back_populates="match",
        cascade="all, delete-orphan",
    )

    # ==========================================================
    # Betting
    # ==========================================================

    betting_odds = relationship(
        "BettingOdds",
        back_populates="match",
        cascade="all, delete-orphan",
    )

    # ==========================================================
    # Machine Learning
    # ==========================================================

    predictions = relationship(
        "Prediction",
        back_populates="match",
        cascade="all, delete-orphan",
    )

    # ==========================================================
    # Representation
    # ==========================================================

    def __repr__(self):
        home = (
            self.home_team.name
            if self.home_team
            else "Unknown"
        )

        away = (
            self.away_team.name
            if self.away_team
            else "Unknown"
        )

        return f"<Match({home} vs {away})>"


event.listen(Match, "before_insert", _validate_match_insert)
event.listen(Match, "before_update", _validate_match_update)
