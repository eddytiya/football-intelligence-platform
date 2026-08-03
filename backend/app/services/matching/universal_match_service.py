from sqlalchemy.orm import Session

from app.models.match import Match
from app.services.matching.match_resolver import MatchResolver
from app.services.matching.merge_service import MergeService


class UniversalMatchService:
    """
    Universal service responsible for deciding whether
    an incoming match should be inserted or merged.
    """

    def __init__(self, db: Session):
        self.db = db
        self.resolver = MatchResolver(db)
        self.merger = MergeService()

    def process_match(
        self,
        incoming_match: Match,
    ) -> tuple[Match, bool]:
        """
        Returns
        -------
        (match, inserted)

        inserted=True
            New match.

        inserted=False
            Existing match was merged.
        """

        existing = self.resolver.find_existing_match(
            incoming_match
        )

        if existing is None:

            self.db.add(incoming_match)

            return incoming_match, True

        existing = self.merger.merge_match(
            existing,
            incoming_match,
        )

        return existing, False