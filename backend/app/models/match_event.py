from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship

from app.db.base import Base


class MatchEvent(Base):
    __tablename__ = "match_events"

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

    assist_player_id = Column(
        Integer,
        ForeignKey("players.id"),
        nullable=True,
    )

    # ===========================
    # Event Information
    # ===========================

    minute = Column(Integer, nullable=False)

    extra_minute = Column(Integer)

    event_type = Column(
        String(50),
        nullable=False,
    )

    detail = Column(String)

    comments = Column(String)

    # ===========================
    # Relationships
    # ===========================

    match = relationship(
        "Match",
        back_populates="events",
    )

    team = relationship(
        "Team",
        back_populates="events",
    )

    player = relationship(
        "Player",
        foreign_keys=[player_id],
        back_populates="events",
    )

    assist_player = relationship(
        "Player",
        foreign_keys=[assist_player_id],
        back_populates="assists",
    )

    def __repr__(self):
        return (
            f"<MatchEvent("
            f"{self.event_type} "
            f"{self.minute}')>"
        )