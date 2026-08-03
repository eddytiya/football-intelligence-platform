from datetime import datetime, timedelta

from app.models.sync_log import SyncLog
from app.repositories.sync_repository import SyncRepository


class SyncService:
    """
    Handles synchronization state for ETL jobs.
    """

    DEFAULT_LOOKBACK_DAYS = 30

    def __init__(self, sync_repository: SyncRepository):
        self.sync_repository = sync_repository

    def get_sync_window(
        self,
        provider: str,
        resource: str,
    ) -> tuple[datetime, datetime]:
        """
        Returns the synchronization window.
        """

        now = datetime.utcnow()

        last_sync = self.sync_repository.get_last_successful_sync(
            provider,
            resource,
        )

        if last_sync is None:
            return (
                now - timedelta(days=self.DEFAULT_LOOKBACK_DAYS),
                now,
            )

        start = last_sync.last_sync - timedelta(days=1)

        if start >= now:
            start = now - timedelta(minutes=1)

        return (
            start,
            now,
        )

    def create_sync_log(
        self,
        provider: str,
        resource: str,
    ) -> SyncLog:
        """
        Creates a new synchronization log.
        """

        sync_log = SyncLog(
            provider=provider,
            resource=resource,
            status="RUNNING",
            last_sync=datetime.utcnow(),
            records_processed=0,
            records_inserted=0,
            records_updated=0,
            duration_seconds=0,
        )

        return self.sync_repository.create_sync_log(
            sync_log
        )

    def complete_sync(
        self,
        sync_log: SyncLog,
        processed: int,
        inserted: int,
        updated: int,
        duration: float,
    ) -> SyncLog:
        """
        Marks synchronization as successful.
        """

        sync_log.status = "SUCCESS"
        sync_log.last_sync = datetime.utcnow()

        sync_log.records_processed = processed
        sync_log.records_inserted = inserted
        sync_log.records_updated = updated
        sync_log.duration_seconds = duration

        return self.sync_repository.update_sync_log(
            sync_log
        )

    def fail_sync(
        self,
        sync_log: SyncLog,
        duration: float,
    ) -> SyncLog:
        """
        Marks synchronization as failed.
        """

        sync_log.status = "FAILED"
        sync_log.duration_seconds = duration

        return self.sync_repository.update_sync_log(
            sync_log
        )