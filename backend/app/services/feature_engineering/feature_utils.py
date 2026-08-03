from datetime import datetime

from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.models.match import Match


def get_previous_matches(
    db: Session,
    team_id: int,
    before_date: datetime,
    limit: int = 5,
):
    """
    Returns the most recent finished matches played by a team
    before the specified date.

    Parameters
    ----------
    db : Session
        SQLAlchemy database session.

    team_id : int
        Team ID.

    before_date : datetime
        Only matches before this date are returned.

    limit : int, default=5
        Number of previous matches to return.

    Returns
    -------
    list[Match]
        List of Match objects ordered from newest to oldest.
    """

    return (
        db.query(Match)
        .filter(
            Match.status == "FINISHED",
            Match.utc_date < before_date,
            or_(
                Match.home_team_id == team_id,
                Match.away_team_id == team_id,
            ),
        )
        .order_by(Match.utc_date.desc())
        .limit(limit)
        .all()
    )


def calculate_points(matches, team_id: int) -> int:
    """
    Calculate the total points earned by a team.

    Win  = 3 points
    Draw = 1 point
    Loss = 0 points
    """

    points = 0

    for match in matches:

        # Team played at home
        if match.home_team_id == team_id:

            if match.home_score > match.away_score:
                points += 3

            elif match.home_score == match.away_score:
                points += 1

        # Team played away
        elif match.away_team_id == team_id:

            if match.away_score > match.home_score:
                points += 3

            elif match.away_score == match.home_score:
                points += 1

    return points