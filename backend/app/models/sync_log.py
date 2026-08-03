from datetime import datetime

from sqlalchemy import (
    Column,
    DateTime,
    Float,
    Integer,
    String,
)

from app.db.base import Base


class SyncLog(Base):
    """
    Stores synchronization history for every ETL run.

    Each record represents one synchronization attempt.
    """

    __tablename__ = "sync_logs"

    id = Column(
        Integer,
        primary_key=True,
        index=True,
    )

    # Data provider
    provider = Column(
        String(50),
        nullable=False,
        index=True,
    )

    # matches, teams, players, standings...
    resource = Column(
        String(50),
        nullable=False,
        index=True,
    )

    # SUCCESS / FAILED
    status = Column(
        String(20),
        nullable=False,
    )

    # Last successful synchronization timestamp
    last_sync = Column(
        DateTime,
        nullable=False,
    )

    # Number of records processed
    records_processed = Column(
        Integer,
        nullable=False,
        default=0,
    )

    # Newly inserted rows
    records_inserted = Column(
        Integer,
        nullable=False,
        default=0,
    )

    # Updated rows
    records_updated = Column(
        Integer,
        nullable=False,
        default=0,
    )

    # ETL duration in seconds
    duration_seconds = Column(
        Float,
        nullable=False,
        default=0.0,
    )

    # Log creation timestamp
    created_at = Column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )

    def __repr__(self):

        return (
            f"<SyncLog("
            f"{self.provider}, "
            f"{self.resource}, "
            f"{self.status}"
            f")>"
        )