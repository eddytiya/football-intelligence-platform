from datetime import date
from typing import List

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.competition import (
    CompetitionResponse,
)
from app.services.competition_service import (
    CompetitionService,
)
from app.models.competition import Competition
from app.models.player_season_scorer import PlayerSeasonScorer
from app.services.football_api import FootballAPIClient

router = APIRouter(
    prefix="/competitions",
    tags=["Competitions"],
)


@router.get(
    "",
    response_model=List[CompetitionResponse],
)
def get_competitions(
    db: Session = Depends(get_db),
):
    """
    Return all football competitions.
    """

    service = CompetitionService(db)

    return service.get_all_competitions()


@router.get("/{competition_id}/top-scorers/decade")
def get_decade_top_scorers(competition_id: int, db: Session = Depends(get_db)):
    """Cache available official scorer tables, then aggregate the last ten seasons."""
    competition = db.query(Competition).filter(Competition.id == competition_id).first()
    if competition is None or not competition.code:
        return {"competition": None, "coverage": [], "scorers": [], "message": "This competition has no provider code for scorer imports."}

    years = list(range(date.today().year - 10, date.today().year))
    # A previous empty/provider response must not permanently mark a season as imported.
    cached_years = {row[0] for row in db.query(PlayerSeasonScorer.season_year).filter(PlayerSeasonScorer.competition_id == competition_id, (PlayerSeasonScorer.goals > 0) | (PlayerSeasonScorer.appearances > 0)).distinct()}
    client = FootballAPIClient()
    for year in years:
        if year in cached_years:
            continue
        payload = client.get(f"/competitions/{competition.code}/scorers", {"season": year, "limit": 30})
        if not payload:
            continue
        for item in payload.get("scorers", []):
            player = item.get("player") or {}
            team = item.get("team") or {}
            api_id = player.get("id")
            if not api_id:
                continue
            row = db.query(PlayerSeasonScorer).filter_by(competition_id=competition_id, season_year=year, player_api_id=api_id).first()
            if row is None:
                row = PlayerSeasonScorer(competition_id=competition_id, season_year=year, player_api_id=api_id, player_name=player.get("name") or "Unknown player")
                db.add(row)
            row.player_name = player.get("name") or row.player_name
            row.team_name = team.get("name")
            row.team_crest = team.get("crest")
            row.goals = item.get("goals", item.get("numberOfGoals", 0)) or 0
            row.assists = item.get("assists", item.get("numberOfAssists", 0)) or 0
            row.appearances = item.get("playedMatches", item.get("numberOfPlayedMatches", 0)) or 0
        db.commit()

    # Do not present placeholder zero-value rows as a real scorer leaderboard.
    rows = db.query(PlayerSeasonScorer).filter(
        PlayerSeasonScorer.competition_id == competition_id,
        (PlayerSeasonScorer.goals > 0) | (PlayerSeasonScorer.appearances > 0),
    ).all()
    coverage = sorted({row.season_year for row in rows})
    totals = {}
    for row in rows:
        entry = totals.setdefault(row.player_api_id, {"player": row.player_name, "goals": 0, "assists": 0, "appearances": 0, "seasons": [], "club": row.team_name, "crest": row.team_crest})
        entry["goals"] += row.goals; entry["assists"] += row.assists; entry["appearances"] += row.appearances; entry["seasons"].append(row.season_year)
        if row.goals >= entry.get("best_season_goals", -1): entry["club"], entry["crest"], entry["best_season_goals"] = row.team_name, row.team_crest, row.goals
    scorers = sorted(totals.values(), key=lambda item: (-item["goals"], -item["assists"], item["player"]))[:20]
    return {"competition": competition.name, "coverage": coverage, "scorers": scorers, "message": None if coverage else "No scorer seasons are available through the current provider access."}
