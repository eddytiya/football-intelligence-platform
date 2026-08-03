from sqlalchemy import (
    Boolean,
    Column,
    Float,
    ForeignKey,
    Integer,
)
from sqlalchemy.orm import relationship

from app.db.base import Base


class TeamStatistics(Base):
    __tablename__ = "team_statistics"

    id = Column(Integer, primary_key=True, index=True)

    # ==========================================================
    # Relationships
    # ==========================================================

    match_id = Column(
        Integer,
        ForeignKey("matches.id"),
        nullable=False,
        index=True,
    )

    team_id = Column(
        Integer,
        ForeignKey("teams.id"),
        nullable=False,
        index=True,
    )

    # ==========================================================
    # Possession
    # ==========================================================

    possession = Column(Float)

    # ==========================================================
    # Shooting
    # ==========================================================

    shots = Column(Integer, default=0)

    shots_on_target = Column(Integer, default=0)

    shots_off_target = Column(Integer, default=0)

    blocked_shots = Column(Integer, default=0)

    shots_inside_box = Column(Integer)

    shots_outside_box = Column(Integer)

    expected_goals = Column(Float)

    # ==========================================================
    # Passing
    # ==========================================================

    passes = Column(Integer, default=0)

    accurate_passes = Column(Integer, default=0)

    pass_accuracy = Column(Float)

    # ==========================================================
    # Attacking
    # ==========================================================

    corners = Column(Integer, default=0)

    offsides = Column(Integer, default=0)

    big_chances = Column(Integer)

    big_chances_missed = Column(Integer)

    # ==========================================================
    # Defensive
    # ==========================================================

    tackles = Column(Integer, default=0)

    interceptions = Column(Integer, default=0)

    clearances = Column(Integer, default=0)

    saves = Column(Integer, default=0)

    blocked_passes = Column(Integer)

    # ==========================================================
    # Discipline
    # ==========================================================

    fouls = Column(Integer, default=0)

    yellow_cards = Column(Integer, default=0)

    red_cards = Column(Integer, default=0)

    # ==========================================================
    # Duels
    # ==========================================================

    aerial_duels_won = Column(Integer)

    aerial_duels_lost = Column(Integer)

    dribbles = Column(Integer)

    successful_dribbles = Column(Integer)

    # ==========================================================
    # Goalkeeper
    # ==========================================================

    clean_sheet = Column(Boolean)

    penalties_saved = Column(Integer)

    # ==========================================================
    # Relationships
    # ==========================================================

    match = relationship(
        "Match",
        back_populates="team_statistics",
    )

    team = relationship(
        "Team",
        back_populates="team_statistics",
    )

    def __repr__(self):
        return (
            f"<TeamStatistics("
            f"match={self.match_id}, "
            f"team={self.team_id})>"
        )