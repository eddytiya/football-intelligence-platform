from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.db.base import Base


class Competition(Base):
    __tablename__ = "competitions"

    id = Column(Integer, primary_key=True, index=True)

    # Football-Data API ID
    api_id = Column(Integer, unique=True, nullable=False)

    # Competition Information
    name = Column(String(150), nullable=False)

    code = Column(String(10), unique=True, nullable=False)

    type = Column(String(30), nullable=False)

    # Area Information
    area_name = Column(String(100), nullable=False)

    area_code = Column(String(10), nullable=False)

    area_flag = Column(String(255))

    # Competition Logo
    emblem = Column(String(255))

    # Number of seasons available
    seasons_available = Column(Integer)

    # ===========================
    # Relationships
    # ===========================

    competition_teams = relationship(
        "CompetitionTeam",
        back_populates="competition",
        cascade="all, delete-orphan",
    )
    

    seasons = relationship(
        "Season",
        back_populates="competition",
        cascade="all, delete-orphan",
    )

    matches = relationship(
        "Match",
        back_populates="competition",
        cascade="all, delete-orphan",
    )

    standings = relationship(
        "Standing",
        back_populates="competition",
        cascade="all, delete-orphan",
    )

    # ===========================
    # Timestamps
    # ===========================

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
    )

    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )

    def __repr__(self):
        return f"<Competition(name='{self.name}', code='{self.code}')>"