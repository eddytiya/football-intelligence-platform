from sqlalchemy import (
    Column,
    ForeignKey,
    Integer,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship

from app.db.base import Base


class CompetitionMapping(Base):
    __tablename__ = "competition_mappings"

    id = Column(
        Integer,
        primary_key=True,
        index=True,
    )

    competition_id = Column(
        Integer,
        ForeignKey(
            "competitions.id",
            ondelete="CASCADE",
        ),
        nullable=False,
    )

    provider = Column(
        String(50),
        nullable=False,
    )

    provider_id = Column(
        Integer,
        nullable=False,
    )

    competition = relationship(
        "Competition",
        back_populates="provider_mappings",
    )

    __table_args__ = (
        UniqueConstraint(
            "provider",
            "provider_id",
            name="uq_competition_provider",
        ),
    )

    def __repr__(self):
        return (
            f"<CompetitionMapping("
            f"{self.provider}:{self.provider_id}"
            f")>"
        )