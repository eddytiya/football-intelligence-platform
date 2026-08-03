from sqlalchemy import Column, Integer, String, Float
from sqlalchemy.orm import relationship

from app.db.base import Base


class Stadium(Base):
    __tablename__ = "stadiums"

    # Primary Key
    id = Column(Integer, primary_key=True, index=True)

    # External API ID
    api_id = Column(
        Integer,
        unique=True,
        nullable=True,
    )

    # Stadium Information
    name = Column(
        String,
        unique=True,
        nullable=False,
    )

    city = Column(String)

    country = Column(String)

    address = Column(String)

    capacity = Column(Integer)

    surface = Column(String)

    opened_year = Column(Integer)

    latitude = Column(Float)

    longitude = Column(Float)

    timezone = Column(String)

    # Relationships

    teams = relationship(
        "Team",
        back_populates="stadium",
    )

    matches = relationship(
        "Match",
        back_populates="stadium",
    )

    def __repr__(self):
        return f"<Stadium(name='{self.name}')>"