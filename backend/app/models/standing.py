from sqlalchemy import Column, ForeignKey, Integer
from sqlalchemy.orm import relationship

from app.db.base import Base


class Standing(Base):
    __tablename__ = "standings"

    id = Column(Integer, primary_key=True, index=True)

    competition_id = Column(
        Integer,
        ForeignKey("competitions.id"),
        nullable=False,
    )

    season_id = Column(
        Integer,
        ForeignKey("seasons.id"),
        nullable=False,
    )

    team_id = Column(
        Integer,
        ForeignKey("teams.id"),
        nullable=False,
    )

    position = Column(Integer, nullable=False)

    played_games = Column(Integer, nullable=False)

    won = Column(Integer, nullable=False)

    draw = Column(Integer, nullable=False)

    lost = Column(Integer, nullable=False)

    points = Column(Integer, nullable=False)

    goals_for = Column(Integer, nullable=False)

    goals_against = Column(Integer, nullable=False)

    goal_difference = Column(Integer, nullable=False)

    competition = relationship(
        "Competition",
        back_populates="standings",
    )

    season = relationship(
        "Season",
        back_populates="standings",
    )

    team = relationship(
        "Team",
        back_populates="standings",
    )