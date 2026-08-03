from datetime import timedelta

from app.models.match import Match


class MatchMatcher:
    """
    Determines whether two matches represent
    the same real-world football fixture.

    Matching Strategy
    -----------------
    1. Same API ID -> Match
    2. Same home & away teams
    3. Same competition
    4. Same season
    5. Match dates within tolerance
    """

    DATE_TOLERANCE = timedelta(days=1)

    def is_same_match(
        self,
        existing_match: Match,
        incoming_match: Match,
    ) -> bool:
        """
        Returns True if the two matches
        represent the same football fixture.
        """

        # Same external API match
        if (
            existing_match.api_id
            and incoming_match.api_id
            and existing_match.api_id == incoming_match.api_id
        ):
            return True

        # Home team
        if existing_match.home_team_id != incoming_match.home_team_id:
            return False

        # Away team
        if existing_match.away_team_id != incoming_match.away_team_id:
            return False

        # Competition
        if existing_match.competition_id != incoming_match.competition_id:
            return False

        # Season
        if existing_match.season_id != incoming_match.season_id:
            return False

        # Match date
        if (
            existing_match.match_date is not None
            and incoming_match.match_date is not None
        ):
            difference = abs(
                existing_match.match_date -
                incoming_match.match_date
            )

            if difference > self.DATE_TOLERANCE:
                return False

        return True