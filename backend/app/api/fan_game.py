import logging
import math
from datetime import datetime, timezone
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, joinedload

from app.api.auth import current_user
from app.api.prediction import get_historical_prediction
from app.db.session import get_db
from app.models.fan_pick import FanPick
from app.models.match import Match
from app.models.user import User

router = APIRouter(prefix="/fan-game", tags=["Fan vs model"])
logger = logging.getLogger(__name__)
OUTCOMES = ("home", "draw", "away")


def utc(value):
    return value.replace(tzinfo=timezone.utc) if value and value.tzinfo is None else value


def valid_probabilities(values):
    return isinstance(values, dict) and all(type(values.get(key)) in (int, float) and math.isfinite(values[key]) and 0 <= values[key] <= 1 for key in OUTCOMES) and abs(sum(values[key] for key in OUTCOMES) - 1) <= 0.0001


def require_open(match, now):
    if not match:
        raise HTTPException(404, "Fixture not found.")
    if match.status not in {"SCHEDULED", "TIMED"} or not match.utc_date or utc(match.utc_date) <= now:
        raise HTTPException(409, "Picks are locked. Only verified fixtures before kickoff accept picks.")


def pick_payload(row, match, now):
    payload = {"match_id": row.match_id, "outcome": row.outcome, "saved_at": utc(row.created_at),
               "kickoff_at_capture": utc(row.kickoff_at_capture), "model_probabilities": row.model_probabilities,
               "model_version": row.model_version, "home_team_name": match.home_team.name,
               "away_team_name": match.away_team.name, "utc_date": utc(match.utc_date),
               "competition_name": match.competition.name if match.competition else "Unknown competition",
               "status": match.status, "home_score": match.home_score, "away_score": match.away_score,
               "state": "pending"}
    if (not match.utc_date or utc(row.created_at) >= utc(match.utc_date) or utc(row.created_at) >= utc(row.kickoff_at_capture)
            or row.home_team_id != match.home_team_id or row.away_team_id != match.away_team_id):
        payload["state"] = "excluded"
    elif match.status in {"CANCELLED", "POSTPONED", "QUARANTINED", "AWARDED"}:
        payload["state"] = "excluded"
    elif match.status == "FINISHED":
        if utc(match.utc_date) > now or not all(type(score) is int and score >= 0 for score in [match.home_score, match.away_score]):
            payload["state"] = "excluded"
        else:
            actual = "home" if match.home_score > match.away_score else "away" if match.home_score < match.away_score else "draw"
            payload.update(state="settled", actual=actual, fan_correct=row.outcome == actual)
            if valid_probabilities(row.model_probabilities) and (row.model_version or '').startswith('historical-season-v3-'):
                picked = max(OUTCOMES, key=lambda key: row.model_probabilities[key])
                payload.update(model_pick=picked, model_correct=picked == actual)
    return payload


class PickInput(BaseModel):
    match_id: int = Field(ge=1)
    outcome: Literal["home", "draw", "away"]


@router.get("/picks")
def get_picks(user: User = Depends(current_user), db: Session = Depends(get_db)):
    rows = db.query(FanPick, Match).join(Match, Match.id == FanPick.match_id).options(
        joinedload(Match.home_team), joinedload(Match.away_team), joinedload(Match.competition),
    ).filter(FanPick.user_id == user.id).order_by(FanPick.created_at.desc()).all()
    now = datetime.now(timezone.utc)
    return [pick_payload(row, match, now) for row, match in rows]


@router.post("/picks", status_code=201)
def submit_pick(payload: PickInput, user: User = Depends(current_user), db: Session = Depends(get_db)):
    match = db.query(Match).filter(Match.id == payload.match_id).first()
    require_open(match, datetime.now(timezone.utc))
    if db.query(FanPick).filter_by(user_id=user.id, match_id=payload.match_id).first():
        raise HTTPException(409, "Your pick is already locked for this fixture.")
    identity = (match.home_team_id, match.away_team_id, match.utc_date)
    probabilities = None
    version = None
    try:
        forecast = get_historical_prediction(payload.match_id, db)
        candidate = {"home": forecast.get("home_win_probability"), "draw": forecast.get("draw_probability"), "away": forecast.get("away_win_probability")}
        if forecast.get("prediction_status") == "ready" and valid_probabilities(candidate):
            probabilities, version = candidate, forecast.get("model_version")
    except HTTPException:
        pass  # A fan pick remains useful when no verified model forecast exists.
    except Exception:
        logger.exception("Model snapshot unavailable for fan pick %s", payload.match_id)
    # Model inference may have taken us past kickoff, or the fixture may have changed.
    match = db.query(Match).populate_existing().filter(Match.id == payload.match_id).with_for_update().first()
    now = datetime.now(timezone.utc)
    require_open(match, now)
    if identity != (match.home_team_id, match.away_team_id, match.utc_date):
        raise HTTPException(409, "The fixture changed while saving. Refresh and choose again.")
    row = FanPick(user_id=user.id, match_id=match.id, outcome=payload.outcome, created_at=now.replace(tzinfo=None),
                  kickoff_at_capture=utc(match.utc_date).replace(tzinfo=None), home_team_id=match.home_team_id,
                  away_team_id=match.away_team_id, model_probabilities=probabilities, model_version=version)
    db.add(row)
    try:
        db.commit(); db.refresh(row)
    except IntegrityError:
        db.rollback()
        raise HTTPException(409, "Your pick is already locked for this fixture.")
    return pick_payload(row, match, datetime.now(timezone.utc))
