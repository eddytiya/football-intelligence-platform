from sqlalchemy import Column, Integer, String, Date, ForeignKey
from sqlalchemy.orm import relationship

from app.db.base import Base


class Coach(Base):
    __tablename__ = "coaches"

    id = Column(Integer, primary_key=True, index=True)

    # Football API ID
    api_id = Column(Integer, unique=True, nullable=True)

    team_id = Column(
        Integer,
        ForeignKey("teams.id"),
        nullable=False,
    )

    name = Column(String, nullable=False)

    first_name = Column(String)

    last_name = Column(String)

    date_of_birth = Column(Date)

    nationality = Column(String)

    contract_start = Column(Date)

    contract_end = Column(Date)

    photo = Column(String)

    last_updated = Column(String)

    # Relationships
    team = relationship(
        "Team",
        back_populates="coach",
    )

    def __repr__(self):
        return f"<Coach(name='{self.name}')>"