from sqlalchemy import (
    Column,
    Float,
    ForeignKey,
    Integer,
    String,
)
from sqlalchemy.orm import relationship

from app.db.base import Base


class BettingOdds(Base):
    """
    Stores betting odds for a match from different bookmakers.

    One row represents one bookmaker's odds for one match.

    Example
    -------
    Match: Arsenal vs Chelsea

    Bet365
        Home : 2.10
        Draw : 3.40
        Away : 3.20

    Pinnacle
        Home : 2.05
        Draw : 3.50
        Away : 3.25
    """

    __tablename__ = "betting_odds"

    # ==========================================================
    # Primary Key
    # ==========================================================

    id = Column(
        Integer,
        primary_key=True,
        index=True,
    )

    # ==========================================================
    # Relationships
    # ==========================================================

    match_id = Column(
        Integer,
        ForeignKey("matches.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # ==========================================================
    # Bookmaker Information
    # ==========================================================

    bookmaker = Column(
        String(50),
        nullable=False,
        index=True,
    )

    # ==========================================================
    # Full Time Odds
    # ==========================================================

    home_win = Column(Float)

    draw = Column(Float)

    away_win = Column(Float)

    # ==========================================================
    # Over / Under 2.5 Goals
    # ==========================================================

    over_2_5 = Column(Float)

    under_2_5 = Column(Float)

    # ==========================================================
    # Both Teams To Score
    # ==========================================================

    btts_yes = Column(Float)

    btts_no = Column(Float)

    # ==========================================================
    # Asian Handicap
    # ==========================================================

    handicap = Column(Float)

    handicap_home = Column(Float)

    handicap_away = Column(Float)

    # ==========================================================
    # Double Chance
    # ==========================================================

    home_draw = Column(Float)

    home_away = Column(Float)

    draw_away = Column(Float)

    # ==========================================================
    # Relationships
    # ==========================================================

    match = relationship(
        "Match",
        back_populates="betting_odds",
    )

    def __repr__(self):
        return (
            f"<BettingOdds("
            f"match={self.match_id}, "
            f"bookmaker='{self.bookmaker}')>"
        )