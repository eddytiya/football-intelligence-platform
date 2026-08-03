from datetime import datetime
import re

from sqlalchemy import or_, func,and_
from sqlalchemy.orm import Session, aliased, joinedload

from app.models.match import Match
from app.models.team import Team
from datetime import date, datetime, timedelta

class MatchRepository:
    """
    Repository responsible for all database operations
    related to football matches.

    This class ONLY interacts with the database.

    Responsibilities
    ----------------
    - Retrieve matches
    - Retrieve previous matches
    - Retrieve finished matches

    This class DOES NOT:
    - Calculate football statistics
    - Generate ML features
    - Train models
    """

    def __init__(self, db: Session):
        """
        Initialize the repository.

        Parameters
        ----------
        db : Session
            SQLAlchemy database session.
        """
        self.db = db

    def get_match_by_id(
        self,
        match_id: int,
    ) -> Match | None:
        """
        Return a match by its database ID.
        """

        return (
            self.db.query(Match)
            .options(
                joinedload(Match.competition),
                joinedload(Match.home_team),
                joinedload(Match.away_team),
            )
            .filter(Match.id == match_id)
            .first()
        )

    def get_finished_matches(self) -> list[Match]:
        """
        Return all finished matches ordered
        by match date.
        """

        return (
            self.db.query(Match)
            .filter(Match.status == "FINISHED")
            .order_by(Match.utc_date.asc())
            .all()
        )

    def get_previous_matches(
        self,
        team_id: int,
        before_date: datetime,
        limit: int = 5,
    ) -> list[Match]:
        """
        Return the team's previous finished matches.
        """

        query = (
            self.db.query(Match)
            .filter(
                Match.status == "FINISHED",
                or_(
                    Match.home_team_id == team_id,
                    Match.away_team_id == team_id,
                ),
            )
        )

        # ---------------------------------------------------------
        # Prefer utc_date when available.
        # Fall back to match_date for older historical matches.
        # ---------------------------------------------------------

        if before_date is not None:

            query = query.filter(
                or_(
                    Match.utc_date < before_date,
                    and_(
                        Match.utc_date.is_(None),
                        Match.match_date < before_date.date(),
                    ),
                )
            )

        return (
            query.order_by(
                Match.match_date.desc(),
                Match.utc_date.desc(),
            )
            .limit(limit)
            .all()
        )
    
    def get_head_to_head_matches(
        self,
        home_team_id: int,
        away_team_id: int,
        before_date: datetime,
        limit: int = 5,
    ) -> list[Match]:
        """
        Return previous matches played between two teams.
        """

        return (
            self.db.query(Match)
            .filter(
                Match.status == "FINISHED",
                Match.utc_date < before_date,
                or_(
                    (
                        (Match.home_team_id == home_team_id)
                        & (Match.away_team_id == away_team_id)
                    ),
                    (
                        (Match.home_team_id == away_team_id)
                        & (Match.away_team_id == home_team_id)
                    ),
                ),
            )
            .order_by(Match.utc_date.desc())
            .limit(limit)
            .all()
        )
    
    def get_finished_matches_before(
        self,
        before_date: datetime,
    ) -> list[Match]:
        """
        Return all finished matches before the given date.

        Parameters
        ----------
        before_date : datetime
            Only matches before this date are returned.

        Returns
        -------
        list[Match]
        """

        return (
            self.db.query(Match)
            .filter(
                Match.status == "FINISHED",
                Match.utc_date < before_date,
            )
            .order_by(Match.utc_date.asc())
            .all()
        )

    

    def get_upcoming_matches(
        self,
        days: int = 7,
        limit: int | None = None,
    ) -> list[Match]:
        """
        Return upcoming scheduled matches within
        the next N days.
        """

        today = date.today()
        end_date = today + timedelta(days=days)

        query = (
            self.db.query(Match)
            .options(
                joinedload(Match.competition),
                joinedload(Match.home_team),
                joinedload(Match.away_team),
            )
            .filter(
                Match.status == "SCHEDULED",
                Match.match_date >= today,
                Match.match_date <= end_date,
            )
            .order_by(
                Match.match_date.asc(),
                Match.utc_date.asc(),
            )
        )

        if limit is not None:
            query = query.limit(limit)

        return query.all()
    
    def get_next_match(self) -> Match | None:
        """
        Return the next scheduled football match.
        """

        return (
            self.db.query(Match)
            .options(
                joinedload(Match.competition),
                joinedload(Match.home_team),
                joinedload(Match.away_team),
            )
            .filter(
                Match.status == "SCHEDULED",
            )
            .order_by(Match.utc_date.asc())
            .first()
        )

    def get_upcoming_matches_by_competition(
        self,
        competition_id: int,
        limit: int | None = None,
    ) -> list[Match]:
        """
        Return upcoming matches for a competition.

        Parameters
        ----------
        competition_id : int
            Competition database ID.

        limit : int | None, optional
            Maximum number of matches to return.

        Returns
        -------
        list[Match]
        """

        query = (
            self.db.query(Match)
            .filter(
                Match.status == "SCHEDULED",
                Match.competition_id == competition_id,
            )
            .order_by(Match.utc_date.asc())
        )

        if limit is not None:
            query = query.limit(limit)

        return query.all()

    def get_upcoming_matches_by_date(
        self,
        match_date: datetime,
    ) -> list[Match]:
        """
        Return all scheduled matches for a specific date.
        """

        start_of_day = match_date.replace(
            hour=0,
            minute=0,
            second=0,
            microsecond=0,
        )

        end_of_day = match_date.replace(
            hour=23,
            minute=59,
            second=59,
            microsecond=999999,
        )

        return (
            self.db.query(Match)
            .options(
                joinedload(Match.competition),
                joinedload(Match.home_team),
                joinedload(Match.away_team),
            )
            .filter(
                Match.status == "SCHEDULED",
                Match.utc_date >= start_of_day,
                Match.utc_date <= end_of_day,
            )
            .order_by(Match.utc_date.asc())
            .all()
        )
    
    def get_matches_by_date(
        self,
        match_date: datetime,
        status: str | None = None,
    ) -> list[Match]:
        """
        Return matches for a specific date.

        If status is provided, only matches with that
        status are returned.
        """

        start_of_day = match_date.replace(
            hour=0,
            minute=0,
            second=0,
            microsecond=0,
        )

        end_of_day = match_date.replace(
            hour=23,
            minute=59,
            second=59,
            microsecond=999999,
        )

        query = (
            self.db.query(Match)
            .options(
                joinedload(Match.competition),
                joinedload(Match.home_team),
                joinedload(Match.away_team),
            )
            .filter(
                Match.utc_date >= start_of_day,
                Match.utc_date <= end_of_day,
            )
        )

        if status is not None:

            query = query.filter(
                Match.status == status
            )

        return (
            query
            .order_by(Match.utc_date.asc())
            .all()
        )
    
    def get_today_matches(
        self,
        today: datetime,
    ) -> list[Match]:
        """
        Return all scheduled matches for today.
        """

        start_of_day = today.replace(
            hour=0,
            minute=0,
            second=0,
            microsecond=0,
        )

        end_of_day = today.replace(
            hour=23,
            minute=59,
            second=59,
            microsecond=999999,
        )

        return (
            self.db.query(Match)
            .filter(
                Match.status == "SCHEDULED",
                Match.utc_date >= start_of_day,
                Match.utc_date <= end_of_day,
            )
            .order_by(Match.utc_date.asc())
            .all()
        )

    def get_matches_between_dates(
        self,
        start_date: datetime,
        end_date: datetime,
    ) -> list[Match]:
        """
        Return scheduled matches between two dates.
        """

        return (
            self.db.query(Match)
            .filter(
                Match.status == "SCHEDULED",
                Match.utc_date >= start_date,
                Match.utc_date <= end_date,
            )
            .order_by(Match.utc_date.asc())
            .all()
        )

    def search_matches_by_team(self, search_term: str, status: str | None = "SCHEDULED") -> list[Match]:
        """Find a team's matches across all dates, not only the active calendar day."""
        home_team = aliased(Team)
        away_team = aliased(Team)
        query_text = search_term.lower().strip()
        candidates = self.db.query(Team).filter(func.lower(Team.name).like(f"%{query_text}%")).all()

        # Prefer a complete team-name match after removing common club
        # prefixes. This makes "Barcelona" resolve to FC Barcelona rather
        # than also returning RCD Espanyol de Barcelona.
        def canonical(name: str) -> str:
            words = re.sub(r"[^a-z0-9 ]", "", name.lower()).split()
            while words and words[0] in {"fc", "cf", "ac", "afc", "rcd", "rc", "ud", "cd", "sc", "as", "us"}:
                words.pop(0)
            while words and words[-1] in {"fc", "cf", "ac", "afc", "sc"}:
                words.pop()
            return " ".join(words)

        exact_candidates = [team for team in candidates if canonical(team.name) == query_text]
        query = (
            self.db.query(Match)
            .options(joinedload(Match.competition), joinedload(Match.home_team), joinedload(Match.away_team))
            .join(home_team, Match.home_team_id == home_team.id)
            .join(away_team, Match.away_team_id == away_team.id)
        )
        if exact_candidates:
            team_ids = [team.id for team in exact_candidates]
            query = query.filter(or_(Match.home_team_id.in_(team_ids), Match.away_team_id.in_(team_ids)))
        else:
            query = query.filter(or_(
                func.lower(home_team.name).like(f"%{query_text}%"),
                func.lower(away_team.name).like(f"%{query_text}%"),
            ))
        if status:
            query = query.filter(Match.status == status)
        return query.order_by(Match.utc_date.asc()).limit(200).all()

    def get_competition_matchweeks(self, competition_id: int, status: str | None = "SCHEDULED") -> list[int]:
        query = self.db.query(Match.match_week).filter(
            Match.competition_id == competition_id,
            Match.match_week.isnot(None),
        )
        if status:
            query = query.filter(Match.status == status)
        return [week for (week,) in query.distinct().order_by(Match.match_week).all()]

    def get_matches_by_matchweek(self, competition_id: int, match_week: int, status: str | None = "SCHEDULED") -> list[Match]:
        query = self.db.query(Match).options(
            joinedload(Match.competition), joinedload(Match.home_team), joinedload(Match.away_team),
        ).filter(Match.competition_id == competition_id, Match.match_week == match_week)
        if status:
            query = query.filter(Match.status == status)
        return query.order_by(Match.utc_date.asc()).all()

    
    def get_latest_match_date(
        self,
        status: str | None = None,
    ) -> datetime | None:
        """
        Return the latest match date.

        If status is provided, only matches having
        that status are considered.
        """

        query = self.db.query(
            func.max(Match.utc_date)
        )

        if status is not None:

            query = query.filter(
                Match.status == status
            )

        return query.scalar()

    def get_previous_match_date(
        self,
        current_date: datetime,
        status: str | None = None,
    ) -> datetime | None:
        """
        Return the closest previous match date.

        Only returns a date that actually contains
        one or more matches.
        """

        query = (
            self.db.query(
                func.max(Match.utc_date)
            )
            .filter(
                Match.utc_date < current_date
            )
        )

        if status is not None:

            query = query.filter(
                Match.status == status
            )

        return query.scalar()

    def get_next_match_date(
        self,
        current_date: datetime,
        status: str | None = None,
    ) -> datetime | None:
        """
        Return the closest next match date.

        Only returns a date that actually contains
        one or more matches.
        """

        end_of_day = current_date.replace(
            hour=23,
            minute=59,
            second=59,
            microsecond=999999,
        )

        query = (
            self.db.query(
                func.min(Match.utc_date)
            )
            .filter(
                Match.utc_date > end_of_day
            )
        )

        if status is not None:

            query = query.filter(
                Match.status == status
            )

        return query.scalar()

    # ==========================================================
    # Write Operations
    # ==========================================================

    def get_match_by_api_id(
        self,
        api_id: str,
    ) -> Match | None:
        """
        Return a match using the provider's match ID.
        """

        return (
            self.db.query(Match)
            .filter(Match.api_id == api_id)
            .first()
        )


    def create_match(
        self,
        match: Match,
    ) -> Match:
        """
        Insert a new match into the database.
        """

        self.db.add(match)
        self.db.commit()
        self.db.refresh(match)

        return match


    def update_match(
        self,
        match: Match,
    ) -> Match:
        """
        Persist updates to an existing match.
        """

        match = self.db.merge(match)
        self.db.commit()
        self.db.refresh(match)

        return match
