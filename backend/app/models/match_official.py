from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship

from app.db.base import Base


class MatchOfficial(Base):
    __tablename__ = "match_officials"

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

    referee_id = Column(
        Integer,
        ForeignKey("referees.id"),
        nullable=False,
    )

    # ===========================
    # Official Information
    # ===========================

    role = Column(
        String(30),
        nullable=False,
    )

    # ===========================
    # Relationships
    # ===========================

    match = relationship(
        "Match",
        back_populates="officials",
    )

    referee = relationship(
        "Referee",
        back_populates="match_officials",
    )

    def __repr__(self):
        return (
            f"<MatchOfficial("
            f"match_id={self.match_id}, "
            f"role='{self.role}')>"
        )