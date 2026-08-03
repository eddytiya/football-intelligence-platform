from typing import List, Optional

from sqlalchemy.orm import Session

from app.models.sync_log import SyncLog


class SyncRepository:
    """
    Repository for synchronization logs.
    """

    def __init__(self, db: Session):
        self.db = db

    def create_sync_log(self, sync_log: SyncLog) -> SyncLog:
        """
        Create a new synchronization log.
        """

        self.db.add(sync_log)
        self.db.commit()
        self.db.refresh(sync_log)

        return sync_log

    def update_sync_log(self, sync_log: SyncLog) -> SyncLog:
        """
        Update an existing synchronization log.
        """

        self.db.commit()
        self.db.refresh(sync_log)

        return sync_log

    def get_latest_sync(
        self,
        provider: str,
        resource: str,
    ) -> Optional[SyncLog]:
        """
        Returns the latest synchronization attempt.
        """

        return (
            self.db.query(SyncLog)
            .filter(
                SyncLog.provider == provider,
                SyncLog.resource == resource,
            )
            .order_by(SyncLog.created_at.desc())
            .first()
        )

    def get_last_successful_sync(
        self,
        provider: str,
        resource: str,
    ) -> Optional[SyncLog]:
        """
        Returns the most recent successful synchronization.
        """

        return (
            self.db.query(SyncLog)
            .filter(
                SyncLog.provider == provider,
                SyncLog.resource == resource,
                SyncLog.status == "SUCCESS",
            )
            .order_by(SyncLog.created_at.desc())
            .first()
        )

    def get_sync_history(
        self,
        provider: str,
        resource: str,
        limit: int = 20,
    ) -> List[SyncLog]:
        """
        Returns recent synchronization history.
        """

        return (
            self.db.query(SyncLog)
            .filter(
                SyncLog.provider == provider,
                SyncLog.resource == resource,
            )
            .order_by(SyncLog.created_at.desc())
            .limit(limit)
            .all()
        )