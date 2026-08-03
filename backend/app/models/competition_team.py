from sqlalchemy import Column, ForeignKey, Integer, UniqueConstraint
from sqlalchemy.orm import relationship

from app.db.base import Base


class CompetitionTeam(Base):
    __tablename__ = "competition_teams"

    id = Column(Integer, primary_key=True, index=True)

    competition_id = Column(
        Integer,
        ForeignKey("competitions.id"),
        nullable=False,
    )

    team_id = Column(
        Integer,
        ForeignKey("teams.id"),
        nullable=False,
    )

    __table_args__ = (
        UniqueConstraint(
            "competition_id",
            "team_id",
            name="uq_competition_team",
        ),
    )

    competition = relationship(
        "Competition",
        back_populates="competition_teams",
    )

    team = relationship(
        "Team",
        back_populates="competition_teams",
    )