from datetime import date, datetime, time, timedelta, timezone
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import or_
from sqlalchemy.orm import Session, joinedload
from app.api.auth import admin_user
from app.api.prediction import get_historical_model
from app.core.paths import DATA_DIR
from app.db.session import get_db
from app.models.match import Match
from app.models.team import Team
from app.models.forecast_snapshot import ForecastSnapshot
from app.services.prediction.admin_review import actual_outcome, genuine_snapshot, retrospective_prediction, save_snapshot, utc
from app.services.machine_learning.temporal_protocol import verified_cutoffs

router = APIRouter(prefix='/admin/predictions', tags=['Admin predictions'], dependencies=[Depends(admin_user)])


def latest_snapshot(db, match):
    rows = db.query(ForecastSnapshot).filter_by(match_id=match.id).order_by(ForecastSnapshot.generated_at).all()
    # Prefer the first genuine pre-match record over any later replay.
    safe = [row for row in rows if verified_cutoffs(row.payload, match.utc_date) and
            (genuine_snapshot(row, match) or (row.kind == 'walk_forward' and row.payload.get('evaluation_protocol') == 'monthly_walk_forward_v1'))]
    return next((row for row in safe if genuine_snapshot(row, match)), safe[-1] if safe else None)


def match_row(match, snapshot):
    actual = actual_outcome(match)
    forecast = snapshot.payload if snapshot else None
    genuine = genuine_snapshot(snapshot, match) if snapshot else False
    return {'id': match.id, 'utc_date': match.utc_date, 'competition': match.competition.name if match.competition else '',
            'home_team': match.home_team.name if match.home_team else '', 'away_team': match.away_team.name if match.away_team else '',
            'status': match.status, 'home_score': match.home_score, 'away_score': match.away_score,
            'actual_outcome': actual, 'forecast': forecast, 'kind': ('pre_match' if genuine else 'walk_forward') if snapshot else None,
            'generated_at': snapshot.generated_at if snapshot else None,
            'correct': actual == forecast.get('predicted_outcome') if actual and forecast else None}


@router.get('/matches')
def matches(start: date | None = None, end: date | None = None, search: str = '',
            view: str = Query('all', pattern='^(all|past|future)$'),
            offset: int = Query(0, ge=0), limit: int = Query(20, ge=1, le=50), db: Session = Depends(get_db)):
    if start and end and start > end:
        raise HTTPException(422, 'Start date must be before end date.')
    query = db.query(Match).filter(Match.status != 'QUARANTINED')
    if start:
        query = query.filter(Match.utc_date >= datetime.combine(start, time.min))
    if end:
        query = query.filter(Match.utc_date < datetime.combine(end + timedelta(days=1), time.min))
    if view == 'past':
        query = query.filter(Match.utc_date <= datetime.now(timezone.utc).replace(tzinfo=None))
    if view == 'future':
        query = query.filter(Match.utc_date > datetime.now(timezone.utc).replace(tzinfo=None))
    if search.strip():
        term = '%' + search.strip() + '%'
        query = query.filter(or_(Match.home_team.has(Team.name.ilike(term)), Match.away_team.has(Team.name.ilike(term))))
    total = query.count()
    fixtures = query.options(joinedload(Match.home_team), joinedload(Match.away_team), joinedload(Match.competition)).order_by(Match.utc_date.desc(), Match.id.desc()).offset(offset).limit(limit).all()
    return {'total': total, 'rows': [match_row(m, latest_snapshot(db, m)) for m in fixtures], 'offset': offset, 'limit': limit}


@router.get('/performance')
def performance(db: Session = Depends(get_db)):
    rows = db.query(ForecastSnapshot, Match).join(Match, Match.id == ForecastSnapshot.match_id).order_by(ForecastSnapshot.generated_at).all()
    seen, settled, correct = set(), 0, 0
    for snapshot, match in rows:
        if match.id in seen or not genuine_snapshot(snapshot, match) or actual_outcome(match) is None:
            continue
        seen.add(match.id)
        settled += 1
        correct += snapshot.payload.get('predicted_outcome') == actual_outcome(match)
    return {'settled': settled, 'correct': correct, 'accuracy': correct / settled if settled else None,
            'basis': 'First server-saved pre-kickoff forecast per match. Retrospective reviews are excluded.'}


@router.post('/match/{match_id}/review')
def review(match_id: int, db: Session = Depends(get_db)):
    match = db.query(Match).filter_by(id=match_id).first()
    if match is None:
        raise HTTPException(404, 'Match not found.')
    if match.status == 'QUARANTINED' or not match.utc_date or not match.home_team or not match.away_team or not match.competition:
        raise HTTPException(422, 'This fixture needs data review before prediction.')
    stored = latest_snapshot(db, match)
    if stored:
        return match_row(match, stored)
    try:
        upcoming = utc(match.utc_date) > datetime.now(timezone.utc)
        if upcoming:
            model = get_historical_model()
            if match.status not in {'SCHEDULED', 'TIMED'}:
                raise ValueError('Only verified scheduled fixtures can receive a new pre-match forecast.')
            prediction = model.predict_fixture(match.competition.code, match.home_team.name, match.away_team.name, match.utc_date)
        else:
            signature = tuple((p.name, p.stat().st_mtime_ns) for p in sorted((DATA_DIR / 'raw' / 'historical').glob('*.csv')))
            prediction = retrospective_prediction(None, match, signature)
        prediction['match_id'] = match.id
        prediction['review_note'] = ('Saved before kick-off.' if upcoming else
            'Walk-forward backtest: model fitted only on results before this calendar month; form uses earlier days only. Reconstructed from the current historical archive, not a forecast saved before kick-off.')
        snapshot = save_snapshot(db, match, prediction, 'pre_match' if upcoming else 'walk_forward')
        if snapshot is None:
            raise ValueError('Kick-off was reached while generating this forecast. Review again as a retrospective match.')
        return match_row(match, snapshot)
    except (ValueError, FileNotFoundError, RuntimeError) as exc:
        raise HTTPException(422, str(exc)) from exc
