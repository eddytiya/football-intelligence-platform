from sqlalchemy import (
    Column,
    Integer,
    String,
    UniqueConstraint,
    Index,
)

from app.db.base import Base


class ExternalID(Base):
    """
    Stores the mapping between our internal database IDs
    and IDs from external data providers.
    """

    __tablename__ = "external_ids"

    id = Column(
        Integer,
        primary_key=True,
        index=True,
    )

    # competition, team, player, coach...
    entity_type = Column(
        String(50),
        nullable=False,
    )

    # Internal database primary key
    entity_id = Column(
        Integer,
        nullable=False,
    )

    # football-data, statsbomb...
    provider = Column(
        String(50),
        nullable=False,
    )

    # ID from the external provider
    external_id = Column(
        String(255),
        nullable=False,
    )

    __table_args__ = (

        UniqueConstraint(
            "entity_type",
            "provider",
            "external_id",
            name="uq_external_entity",
        ),

        Index(
            "ix_external_lookup",
            "entity_type",
            "provider",
            "external_id",
        ),

        Index(
            "ix_internal_lookup",
            "entity_type",
            "entity_id",
        ),

    )

    def __repr__(self):

        return (
            f"<ExternalID("
            f"{self.entity_type}, "
            f"{self.provider}, "
            f"{self.external_id}"
            f")>"
        )