from sqlalchemy import Column, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from app.db.base import Base


class Team(Base):
    __tablename__ = "teams"

    id = Column(Integer, primary_key=True, index=True)

    # Football-Data API ID
    # Historical teams do not have an API ID.
    api_id = Column(Integer, unique=True, nullable=True)

    # Stadium
    stadium_id = Column(
        Integer,
        ForeignKey("stadiums.id"),
        nullable=True,
    )

    # ===========================
    # Team Information
    # ===========================

    name = Column(String, nullable=False)

    short_name = Column(String)

    tla = Column(String(10))

    crest = Column(String)

    address = Column(String)

    website = Column(String)

    founded = Column(Integer)

    club_colors = Column(String)

    # Temporary until Stadium ETL is completed
    venue = Column(String)

    last_updated = Column(String)

    # ===========================
    # Relationships
    # ===========================

    competition_teams = relationship(
        "CompetitionTeam",
        back_populates="team",
        cascade="all, delete-orphan",
    )

    stadium = relationship(
        "Stadium",
        back_populates="teams",
    )

    coach = relationship(
        "Coach",
        back_populates="team",
        uselist=False,
        cascade="all, delete-orphan",
    )

    home_matches = relationship(
        "Match",
        foreign_keys="Match.home_team_id",
        back_populates="home_team",
    )

    away_matches = relationship(
        "Match",
        foreign_keys="Match.away_team_id",
        back_populates="away_team",
    )

    standings = relationship(
        "Standing",
        back_populates="team",
        cascade="all, delete-orphan",
    )

    players = relationship(
        "Player",
        back_populates="team",
        cascade="all, delete-orphan",
    )

    events = relationship(
        "MatchEvent",
        back_populates="team",
        cascade="all, delete-orphan",
    )

    lineups = relationship(
        "Lineup",
        back_populates="team",
        cascade="all, delete-orphan",
    )

    player_statistics = relationship(
        "PlayerStatistics",
        back_populates="team",
        cascade="all, delete-orphan",
    )

    team_statistics = relationship(
        "TeamStatistics",
        back_populates="team",
        cascade="all, delete-orphan",
    )

    won_seasons = relationship(
        "Season",
        foreign_keys="Season.winner_team_id",
        back_populates="winner",
    )

    def __repr__(self):
        return f"<Team(name='{self.name}')>"