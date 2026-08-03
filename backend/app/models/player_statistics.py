from sqlalchemy import Boolean, Column, ForeignKey, Integer, Float
from sqlalchemy.orm import relationship

from app.db.base import Base


class PlayerStatistics(Base):
    __tablename__ = "player_statistics"

    id = Column(Integer, primary_key=True, index=True)

    # Relationships
    match_id = Column(
        Integer,
        ForeignKey("matches.id"),
        nullable=False,
    )

    player_id = Column(
        Integer,
        ForeignKey("players.id"),
        nullable=False,
    )

    team_id = Column(
        Integer,
        ForeignKey("teams.id"),
        nullable=False,
    )

    # Playing Time
    minutes_played = Column(Integer, default=0)

    started = Column(Boolean, default=False)

    # Attacking
    goals = Column(Integer, default=0)

    assists = Column(Integer, default=0)

    shots = Column(Integer, default=0)

    shots_on_target = Column(Integer, default=0)

    key_passes = Column(Integer, default=0)

    # Passing
    passes = Column(Integer, default=0)

    accurate_passes = Column(Integer, default=0)

    pass_accuracy = Column(Float)

    # Defensive
    tackles = Column(Integer, default=0)

    interceptions = Column(Integer, default=0)

    clearances = Column(Integer, default=0)

    blocks = Column(Integer, default=0)

    # Goalkeeping
    saves = Column(Integer, default=0)

    clean_sheet = Column(Boolean, default=False)

    # Discipline
    fouls = Column(Integer, default=0)

    yellow_cards = Column(Integer, default=0)

    red_cards = Column(Integer, default=0)

    offsides = Column(Integer, default=0)

    # Dribbling
    dribbles = Column(Integer, default=0)

    successful_dribbles = Column(Integer, default=0)

    # Duels
    duels = Column(Integer, default=0)

    duels_won = Column(Integer, default=0)

    # Relationships
    match = relationship(
        "Match",
        back_populates="player_statistics",
    )

    player = relationship(
        "Player",
        back_populates="statistics",
    )

    team = relationship(
        "Team",
        back_populates="player_statistics",
    )

    def __repr__(self):
        return (
            f"<PlayerStatistics(player={self.player_id}, "
            f"match={self.match_id})>"
        )