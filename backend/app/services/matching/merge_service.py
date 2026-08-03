from app.models.match import Match


class MergeService:
    """
    Merges provider data into an existing Match.

    Rules
    -----
    - Never overwrite good data with empty data.
    - Prefer populated values.
    - Update mutable fields such as scores and status.
    """

    def merge_match(
        self,
        existing: Match,
        incoming: Match,
    ) -> Match:
        """
        Merge incoming data into an existing match.

        Returns
        -------
        Updated Match object.
        """

        # ==========================
        # Date & Time
        # ==========================

        if existing.utc_date is None:
            existing.utc_date = incoming.utc_date

        if existing.match_date is None:
            existing.match_date = incoming.match_date

        if existing.kick_off is None:
            existing.kick_off = incoming.kick_off

        # ==========================
        # Stadium
        # ==========================

        if existing.stadium_id is None:
            existing.stadium_id = incoming.stadium_id

        # ==========================
        # Referee
        # ==========================

        if existing.referee_id is None:
            existing.referee_id = incoming.referee_id

        # ==========================
        # Match Information
        # ==========================

        if incoming.status:
            existing.status = incoming.status

        if incoming.stage:
            existing.stage = incoming.stage

        if incoming.match_week:
            existing.match_week = incoming.match_week

        # ==========================
        # Scores
        # ==========================

        existing.home_score = incoming.home_score
        existing.away_score = incoming.away_score

        return existing