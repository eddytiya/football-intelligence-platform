from sqlalchemy import Column, Integer, Boolean, String, ForeignKey
from sqlalchemy.orm import relationship

from app.db.base import Base


class Lineup(Base):
    __tablename__ = "lineups"

    # ===========================
    # Primary Key
    # ===========================

    id = Column(Integer, primary_key=True, index=True)

    # ===========================
    # Foreign Keys
    # ===========================

    match_id = Column(
        Integer,
        ForeignKey("matches.id"),
        nullable=False,
    )

    team_id = Column(
        Integer,
        ForeignKey("teams.id"),
        nullable=False,
    )

    player_id = Column(
        Integer,
        ForeignKey("players.id"),
        nullable=False,
    )

    # ===========================
    # Lineup Information
    # ===========================

    shirt_number = Column(Integer)

    position = Column(String(20))

    formation_position = Column(String(10))

    starter = Column(
        Boolean,
        default=False,
        nullable=False,
    )

    captain = Column(
        Boolean,
        default=False,
        nullable=False,
    )

    minutes_played = Column(Integer)

    # ===========================
    # Relationships
    # ===========================

    match = relationship(
        "Match",
        back_populates="lineups",
    )

    team = relationship(
        "Team",
        back_populates="lineups",
    )

    player = relationship(
        "Player",
        back_populates="lineups",
    )

    def __repr__(self):
        return (
            f"<Lineup("
            f"match_id={self.match_id}, "
            f"player_id={self.player_id})>"
        )