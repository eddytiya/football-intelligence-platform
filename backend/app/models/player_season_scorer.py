from sqlalchemy import Column, ForeignKey, Integer, String, UniqueConstraint

from app.db.base import Base


class PlayerSeasonScorer(Base):
    __tablename__ = "player_season_scorers"
    __table_args__ = (UniqueConstraint("competition_id", "season_year", "player_api_id", name="uq_scorer_competition_season_player"),)

    id = Column(Integer, primary_key=True)
    competition_id = Column(Integer, ForeignKey("competitions.id"), nullable=False, index=True)
    season_year = Column(Integer, nullable=False, index=True)
    player_api_id = Column(Integer, nullable=False)
    player_name = Column(String, nullable=False)
    team_name = Column(String)
    team_crest = Column(String)
    goals = Column(Integer, nullable=False, default=0)
    assists = Column(Integer, nullable=False, default=0)
    appearances = Column(Integer, nullable=False, default=0)
