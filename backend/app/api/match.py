from datetime import date, datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func
from sqlalchemy.orm import Session, joinedload, selectinload

from app.db.session import get_db
from app.schemas.match import (
    MatchDetailResponse,
    UpcomingMatchResponse,
)
from app.services.match_service import MatchService
from app.models.match import Match
from app.models.season import Season
from app.models.standing import Standing
from app.models.team import Team
from app.models.lineup import Lineup
from app.models.match_event import MatchEvent
from app.services.etl.live_score_sync import LiveScoreSync
from app.services.competition_intelligence import CompetitionIntelligenceService

router = APIRouter(
    prefix="/matches",
    tags=["Matches"],
)


@router.get("/{match_id}/centre")
def get_match_centre(match_id: int, db: Session = Depends(get_db)):
    """Return the match-day data already stored locally.

    The response is deliberately explicit about unavailable feeds: weather,
    television and live line-ups are provider data, never estimates.
    """
    match = db.query(Match).options(
        joinedload(Match.home_team), joinedload(Match.away_team), joinedload(Match.competition),
        joinedload(Match.stadium), joinedload(Match.referee),
        selectinload(Match.events).joinedload(MatchEvent.player),
        selectinload(Match.events).joinedload(MatchEvent.assist_player),
        selectinload(Match.lineups).joinedload(Lineup.player),
        selectinload(Match.officials),
    ).filter(Match.id == match_id).first()
    if match is None:
        raise HTTPException(status_code=404, detail="Match not found")
    def club(team):
        return {"id": team.id, "name": team.name, "crest": team.crest}
    events = [{"minute": event.minute, "extra_minute": event.extra_minute, "type": event.event_type,
               "detail": event.detail, "team_id": event.team_id,
               "player": event.player.name if event.player else None,
               "assist": event.assist_player.name if event.assist_player else None} for event in sorted(match.events, key=lambda row: (row.minute, row.extra_minute or 0))]
    lineups = [{"team_id": row.team_id, "player": row.player.name if row.player else "Unknown", "position": row.position,
                "shirt_number": row.shirt_number, "starter": row.starter, "captain": row.captain} for row in match.lineups]
    return {
        "match": {"id": match.id, "status": match.status, "utc_date": match.utc_date, "match_week": match.match_week,
                  "competition": match.competition.name if match.competition else None, "home": club(match.home_team), "away": club(match.away_team),
                  "score": {"home": match.home_score, "away": match.away_score}},
        "events": events, "lineups": lineups,
        "venue": {"name": match.stadium.name, "city": match.stadium.city, "capacity": match.stadium.capacity} if match.stadium else None,
        "referee": match.referee.name if match.referee else None,
        "availability": {"events": bool(events), "lineups": bool(lineups), "venue": bool(match.stadium), "referee": bool(match.referee),
                         "weather": False, "tv": False, "injuries": False},
        "provider_note": "Weather, TV coverage and confirmed injuries appear only after a licensed provider is connected.",
    }


@router.post("/sync/live-scores")
def sync_live_scores(db: Session = Depends(get_db)):
    """Run one score refresh immediately; useful for local development/admin use."""
    return LiveScoreSync(db).run()


@router.get(
    "/upcoming",
    response_model=list[UpcomingMatchResponse],
)
def get_upcoming_matches(
    limit: int | None = None,
    db: Session = Depends(get_db),
):
    """
    Return upcoming scheduled football matches.
    """

    service = MatchService(db)

    return service.get_upcoming_matches(limit)


@router.get(
    "/next",
    response_model=UpcomingMatchResponse,
)
def get_next_match(
    db: Session = Depends(get_db),
):
    """
    Return the next scheduled football match.
    """

    service = MatchService(db)

    match = service.get_next_match()

    if match is None:
        raise HTTPException(
            status_code=404,
            detail="No upcoming matches found.",
        )

    return match


@router.get(
    "/today",
    response_model=list[UpcomingMatchResponse],
)
def get_today_matches(
    db: Session = Depends(get_db),
):
    """
    Return today's scheduled matches.
    """

    service = MatchService(db)

    return service.get_today_matches(datetime.utcnow())


@router.get(
    "/competition/{competition_id}",
    response_model=list[UpcomingMatchResponse],
)
def get_upcoming_matches_by_competition(
    competition_id: int,
    limit: int | None = None,
    db: Session = Depends(get_db),
):
    """
    Return upcoming matches for a competition.
    """

    service = MatchService(db)

    return service.get_upcoming_matches_by_competition(
        competition_id,
        limit,
    )


@router.get(
    "/date/{match_date}",
    response_model=list[MatchDetailResponse],
)
def get_matches_by_date(
    match_date: date,
    status: str | None = None,
    db: Session = Depends(get_db),
):
    """
    Return matches for a specific date.

    Optional query parameter:
        ?status=SCHEDULED
        ?status=FINISHED
        ?status=LIVE
    """

    service = MatchService(db)

    return service.get_matches_by_date(
        match_date=datetime.combine(
            match_date,
            datetime.min.time(),
        ),
        status=status,
    )


@router.get("/latest-date")
def get_latest_match_date(
    status: str | None = Query(
        default=None,
        description="Optional match status",
    ),
    db: Session = Depends(get_db),
):
    """
    Return the latest available match date.

    Examples
    --------
    /matches/latest-date?status=FINISHED
    /matches/latest-date?status=SCHEDULED
    """

    service = MatchService(db)

    latest = service.get_latest_match_date(
        status=status,
    )

    if latest is None:
        raise HTTPException(
            status_code=404,
            detail="No matches found.",
        )

    return {
        "date": latest.date().isoformat(),
    }


@router.get("/month-summary")
def get_month_summary(
    year: int = Query(ge=2010, le=2100),
    month: int = Query(ge=1, le=12),
    status: str | None = None,
    db: Session = Depends(get_db),
):
    """Return match counts per day so the calendar can flag active dates."""
    month_start = date(year, month, 1)
    next_month = date(year + (month == 12), 1 if month == 12 else month + 1, 1)
    rows = db.query(Match.match_date, func.count(Match.id)).filter(
        Match.match_date >= month_start,
        Match.match_date < next_month,
    )
    if status:
        rows = rows.filter(Match.status == status)
    return {
        "days": {
            str(match_date): count
            for match_date, count in rows.group_by(Match.match_date).all()
            if match_date is not None
        }
    }


@router.get("/search", response_model=list[MatchDetailResponse])
def search_matches(
    q: str = Query(min_length=2, max_length=100),
    status: str | None = Query(default="SCHEDULED"),
    db: Session = Depends(get_db),
):
    """Search all fixtures for a team, independent of the selected date."""
    return MatchService(db).search_matches_by_team(q.strip(), status)


@router.get("/competition/{competition_id}/matchweeks")
def get_competition_matchweeks(competition_id: int, status: str | None = Query(default="SCHEDULED"), db: Session = Depends(get_db)):
    return {"matchweeks": MatchService(db).get_competition_matchweeks(competition_id, status)}


@router.get("/competition/{competition_id}/matchweek/{match_week}", response_model=list[MatchDetailResponse])
def get_matches_by_matchweek(competition_id: int, match_week: int, status: str | None = Query(default="SCHEDULED"), db: Session = Depends(get_db)):
    return MatchService(db).get_matches_by_matchweek(competition_id, match_week, status)


@router.get("/competition/{competition_id}/standings-summary")
def get_standings_summary(competition_id: int, db: Session = Depends(get_db)):
    """Return a compact stored standings snapshot for the matchweek view."""
    season_row = db.query(Season.id).filter(Season.competition_id == competition_id).order_by(
        Season.end_year.desc(), Season.id.desc(),
    ).first()
    season_id = season_row[0] if season_row else None
    if season_id is None:
        return {"season": None, "leaders": [], "relegation_zone": []}
    rows = db.query(Standing, Team.name, Team.crest, Season.season_name).join(
        Team, Standing.team_id == Team.id,
    ).join(Season, Standing.season_id == Season.id).filter(
        Standing.competition_id == competition_id, Standing.season_id == season_id,
    ).order_by(Standing.position).all()
    if not rows or max(standing.played_games for standing, *_ in rows) == 0:
        return {"season": rows[0][3] if rows else None, "leaders": [], "relegation_zone": []}
    table = [{"position": standing.position, "team": name, "crest": crest, "points": standing.points} for standing, name, crest, _ in rows]
    return {
        "season": rows[0][3] if rows else None,
        "leaders": table[:4],
        "relegation_zone": table[-3:],
    }


@router.get("/competition/{competition_id}/standings")
def get_competition_standings(competition_id: int, db: Session = Depends(get_db)):
    """Return a current table calculated from the results stored locally.

    The live score sync updates ``matches`` as results arrive. Building the
    table from those rows means the competition page follows those updates
    immediately, rather than waiting for a separate standings import.
    """
    season_row = db.query(Season.id).filter(Season.competition_id == competition_id).order_by(
        Season.end_year.desc(), Season.id.desc(),
    ).first()
    if not season_row:
        return {"season": None, "table": []}
    season_id = season_row[0]
    season = db.query(Season).filter(Season.id == season_id).first()
    matches = db.query(Match).filter(
        Match.competition_id == competition_id,
        Match.season_id == season_id,
    ).all()

    teams = {}
    for match in matches:
        if match.home_team:
            teams[match.home_team_id] = match.home_team
        if match.away_team:
            teams[match.away_team_id] = match.away_team

    table = {
        team_id: {
            "team": team.name, "crest": team.crest, "played": 0, "won": 0,
            "draw": 0, "lost": 0, "goals_for": 0, "goals_against": 0,
            "goal_difference": 0, "points": 0,
        }
        for team_id, team in teams.items()
    }
    finished_statuses = {"FINISHED", "AWARDED"}
    for match in matches:
        if match.status not in finished_statuses or match.home_score is None or match.away_score is None:
            continue
        home, away = table.get(match.home_team_id), table.get(match.away_team_id)
        if not home or not away:
            continue
        home["played"] += 1
        away["played"] += 1
        home["goals_for"] += match.home_score
        home["goals_against"] += match.away_score
        away["goals_for"] += match.away_score
        away["goals_against"] += match.home_score
        if match.home_score > match.away_score:
            home["won"] += 1
            away["lost"] += 1
            home["points"] += 3
        elif match.home_score < match.away_score:
            away["won"] += 1
            home["lost"] += 1
            away["points"] += 3
        else:
            home["draw"] += 1
            away["draw"] += 1
            home["points"] += 1
            away["points"] += 1

    completed_matches = sorted(
        [match for match in matches if match.status in finished_statuses and match.home_score is not None and match.away_score is not None],
        key=lambda match: match.utc_date or datetime.min,
        reverse=True,
    )
    recent_form = {team_id: [] for team_id in table}
    for match in completed_matches:
        home_form, away_form = recent_form.get(match.home_team_id), recent_form.get(match.away_team_id)
        if home_form is None or away_form is None:
            continue
        if match.home_score > match.away_score:
            home_result, away_result = "W", "L"
        elif match.home_score < match.away_score:
            home_result, away_result = "L", "W"
        else:
            home_result = away_result = "D"
        if len(home_form) < 5:
            home_form.append(home_result)
        if len(away_form) < 5:
            away_form.append(away_result)

    for team_id, entry in table.items():
        entry["goal_difference"] = entry["goals_for"] - entry["goals_against"]
        entry["form"] = recent_form[team_id]

    has_results = any(entry["played"] for entry in table.values())
    if has_results:
        ranked = sorted(
            table.values(),
            key=lambda entry: (-entry["points"], -entry["goal_difference"], -entry["goals_for"], entry["team"]),
        )
        return {
            "season": season.season_name if season else None,
            "table": [{"position": index, **entry} for index, entry in enumerate(ranked, start=1)],
            "is_live": True,
        }

    # Do not expose a misleading all-zero table before the season starts.
    return {
        "season": season.season_name if season else None,
        "table": [],
        "is_live": False,
    }


@router.get("/competition/{competition_id}/intelligence")
def get_competition_intelligence(competition_id: int, db: Session = Depends(get_db)):
    """Return simulation-based table projections and form analytics."""
    return CompetitionIntelligenceService(db).get_intelligence(competition_id)


@router.get("/competition/{competition_id}/season-outlook")
def get_competition_season_outlook(competition_id: int, db: Session = Depends(get_db)):
    """Projected current-season table and the five completed seasons behind it."""
    return CompetitionIntelligenceService(db).get_season_outlook(competition_id)


@router.get("/previous-date")
def get_previous_match_date(
    current_date: date,
    status: str | None = Query(
        default=None,
    ),
    db: Session = Depends(get_db),
):
    """
    Return the previous date that contains matches.
    """

    service = MatchService(db)

    previous = service.get_previous_match_date(
        current_date=datetime.combine(
            current_date,
            datetime.min.time(),
        ),
        status=status,
    )

    if previous is None:
        raise HTTPException(
            status_code=404,
            detail="No previous match date found.",
        )

    return {
        "date": previous.date().isoformat(),
    }


@router.get("/next-date")
def get_next_match_date(
    current_date: date,
    status: str | None = Query(
        default=None,
    ),
    db: Session = Depends(get_db),
):
    """
    Return the next date that contains matches.
    """

    service = MatchService(db)

    next_date = service.get_next_match_date(
        current_date=datetime.combine(
            current_date,
            datetime.min.time(),
        ),
        status=status,
    )

    if next_date is None:
        raise HTTPException(
            status_code=404,
            detail="No next match date found.",
        )

    return {
        "date": next_date.date().isoformat(),
    }



@router.get(
    "/{match_id}",
    response_model=MatchDetailResponse,
)
def get_match(
    match_id: int,
    db: Session = Depends(get_db),
):
    """
    Return a match by its ID.
    """

    service = MatchService(db)

    match = service.get_match(match_id)

    if match is None:
        raise HTTPException(
            status_code=404,
            detail="Match not found.",
        )

    return match
