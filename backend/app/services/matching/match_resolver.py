from typing import Optional

from sqlalchemy.orm import Session

from app.models.match import Match
from app.services.matching.match_matcher import MatchMatcher


class MatchResolver:
    """
    Resolves incoming matches against the database.

    Responsibilities
    ----------------
    - Search for an existing match.
    - Determine whether an incoming match already exists.
    - Return the existing match if found.
    """

    def __init__(
        self,
        db: Session,
    ):
        self.db = db
        self.matcher = MatchMatcher()

    def find_existing_match(
        self,
        incoming_match: Match,
    ) -> Optional[Match]:
        """
        Searches for an existing match.

        Returns
        -------
        Match
            Existing database match.

        None
            If no matching record exists.
        """

        candidates = (
            self.db.query(Match)
            .filter(
                Match.competition_id == incoming_match.competition_id,
                Match.season_id == incoming_match.season_id,
            )
            .all()
        )

        for candidate in candidates:

            if self.matcher.is_same_match(
                candidate,
                incoming_match,
            ):
                return candidate

        return None

    def match_exists(
        self,
        incoming_match: Match,
    ) -> bool:
        """
        Returns True if a matching
        record already exists.
        """

        return (
            self.find_existing_match(
                incoming_match
            )
            is not None
        )