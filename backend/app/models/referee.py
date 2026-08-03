from sqlalchemy import Column, Integer, String, Date
from sqlalchemy.orm import relationship

from app.db.base import Base


class Referee(Base):
    __tablename__ = "referees"

    # ===========================
    # Primary Key
    # ===========================

    id = Column(Integer, primary_key=True, index=True)

    # Football-Data API Referee ID
    api_id = Column(Integer, unique=True, nullable=True)

    # ===========================
    # Referee Information
    # ===========================

    name = Column(String, nullable=False)

    first_name = Column(String)

    last_name = Column(String)

    nationality = Column(String)

    date_of_birth = Column(Date)

    photo = Column(String)

    # ===========================
    # Relationships
    # ===========================

    # Legacy relationship (matches.referee_id)
    matches = relationship(
        "Match",
        back_populates="referee",
    )

    # Detailed officiating relationship
    match_officials = relationship(
        "MatchOfficial",
        back_populates="referee",
        cascade="all, delete-orphan",
    )

    def __repr__(self):
        return f"<Referee(name='{self.name}')>"