from sqlalchemy import Column, Integer, String, Date, ForeignKey
from sqlalchemy.orm import relationship

from app.db.base import Base


class Player(Base):
    __tablename__ = "players"

    # ===========================
    # Primary Key
    # ===========================

    id = Column(Integer, primary_key=True, index=True)

    # Football-Data API Player ID
    api_id = Column(Integer, unique=True, nullable=False)

    # ===========================
    # Foreign Key
    # ===========================

    team_id = Column(
        Integer,
        ForeignKey("teams.id"),
        nullable=False,
    )

    # ===========================
    # Player Information
    # ===========================

    name = Column(String, nullable=False)

    first_name = Column(String)

    last_name = Column(String)

    date_of_birth = Column(Date)

    # API-Football's squad endpoint provides age even when it omits an exact
    # date of birth, so retain it as a provider snapshot.
    age = Column(Integer)

    nationality = Column(String)

    position = Column(String)

    shirt_number = Column(Integer)

    last_updated = Column(String)

    # ===========================
    # Relationships
    # ===========================

    team = relationship(
        "Team",
        back_populates="players",
    )

    events = relationship(
        "MatchEvent",
        foreign_keys="MatchEvent.player_id",
        back_populates="player",
        cascade="all, delete-orphan",
    )

    assists = relationship(
        "MatchEvent",
        foreign_keys="MatchEvent.assist_player_id",
        back_populates="assist_player",
        cascade="all, delete-orphan",
    )

    lineups = relationship(
        "Lineup",
        back_populates="player",
        cascade="all, delete-orphan",
    )

    statistics = relationship(
        "PlayerStatistics",
        back_populates="player",
        cascade="all, delete-orphan",
    )

    def __repr__(self):
        return f"<Player(name='{self.name}')>"
