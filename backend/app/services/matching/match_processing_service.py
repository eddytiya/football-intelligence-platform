from sqlalchemy.orm import Session

from app.models.match import Match
from app.services.matching.universal_match_service import (
    UniversalMatchService,
)


class MatchProcessingService:
    """
    Handles the complete lifecycle of processing
    an incoming match.

    Responsibilities
    ----------------
    - Resolve existing matches
    - Merge provider data
    - Insert new matches
    - Flush the SQLAlchemy session
    """

    def __init__(
        self,
        db: Session,
    ):
        self.db = db
        self.universal_service = UniversalMatchService(db)

    def process(
        self,
        incoming_match: Match,
    ) -> Match:
        """
        Process a match and return the canonical Match.
        """

        match = self.universal_service.process_match(
            incoming_match
        )

        self.db.flush()

        return match