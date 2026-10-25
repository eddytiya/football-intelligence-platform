"""Review current-model replays separately from genuine pre-kickoff snapshots."""
from collections import defaultdict, deque
from copy import copy
from datetime import datetime, timezone
from functools import lru_cache
from fastapi.encoders import jsonable_encoder
from sqlalchemy.exc import IntegrityError
from app.models.forecast_snapshot import ForecastSnapshot
from app.services.machine_learning.historical_match_model import TeamState, normalise_team_name
from app.services.machine_learning.temporal_protocol import verified_cutoffs


def utc(value):
    return value.replace(tzinfo=timezone.utc) if value.tzinfo is None else value.astimezone(timezone.utc)


def actual_outcome(match):
    if match.status != 'FINISHED' or match.home_score is None or match.away_score is None:
        return None
    return 'Home Win' if match.home_score > match.away_score else 'Away Win' if match.away_score > match.home_score else 'Draw'


def genuine_snapshot(snapshot, match):
    return (snapshot.kind == 'pre_match' and match.utc_date is not None
            and verified_cutoffs(snapshot.payload, match.utc_date)
            and verified_cutoffs(snapshot.payload, utc(snapshot.generated_at))
            and utc(snapshot.generated_at) < min(utc(snapshot.kickoff_at), utc(match.utc_date)))


def save_snapshot(db, match, payload, kind):
    if not verified_cutoffs(payload, match.utc_date):
        raise ValueError('Forecast is missing verified training and feature cutoffs; it cannot be archived.')
    version = payload['model_version']
    existing = db.query(ForecastSnapshot).filter_by(match_id=match.id, model_version=version, kind=kind).first()
    if existing:
        if kind == 'pre_match' and not genuine_snapshot(existing, match):
            raise ValueError('The stored snapshot no longer passes timing/cutoff checks. It is excluded from performance.')
        return existing
    now = datetime.now(timezone.utc)
    if kind == 'pre_match' and not verified_cutoffs(payload, now):
        raise ValueError('Live forecast data must precede the day on which it is generated.')
    if kind == 'pre_match' and now >= utc(match.utc_date):
        return None
    row = ForecastSnapshot(match_id=match.id, model_version=version, kind=kind,
                           generated_at=now, kickoff_at=utc(match.utc_date), payload=jsonable_encoder(payload))
    try:
        with db.begin_nested():
            db.add(row)
            db.flush()
        db.commit()
    except IntegrityError:
        db.rollback()
        return db.query(ForecastSnapshot).filter_by(match_id=match.id, model_version=version, kind=kind).one()
    return row


@lru_cache(maxsize=16)
def replay_model(model, league, day, history_signature):
    """Rebuild form using strictly earlier days, without changing the shared model."""
    replay = copy(model)
    replay.states = defaultdict(TeamState)
    replay.known_teams = defaultdict(set)
    replay.head_to_head = defaultdict(lambda: deque(maxlen=10))
    replay.league_seasons, replay.league_members = {}, {}
    replay.historical_examples = []
    frame = model.load_matches()
    frame = frame[(frame.league == league) & (frame.match_date < datetime.fromisoformat(day))]
    if frame.empty:
        raise ValueError('No verified history exists before this match for this competition.')
    season_members = set()
    for row in frame.itertuples(index=False):
        # Membership is assembled only from matches already played before cutoff.
        if replay.league_seasons.get(league) != row.season:
            season_members = set()
        season_members.update({row.home_team, row.away_team})
        replay._start_season(league, row.season, season_members)
        replay.league_members[league] = {replay._state_key(league, team) for team in season_members}
        replay.known_teams[league].update({normalise_team_name(row.home_team), normalise_team_name(row.away_team)})
        replay._update_states(league, row.home_team, row.away_team, row.home_goals, row.away_goals, row.match_date)
    return replay


def retrospective_prediction(model, match, signature):
    month = match.utc_date.date().replace(day=1).isoformat()
    frozen = walk_forward_model(month, signature)
    replay = replay_model(frozen, match.competition.code, match.utc_date.date().isoformat(), signature)
    result = replay.predict_fixtures([{'league': match.competition.code, 'home_team': match.home_team.name,
        'away_team': match.away_team.name, 'utc_date': match.utc_date}], reference_time=match.utc_date)[0]
    result['training_cutoff'] = month
    result['evaluation_protocol'] = 'monthly_walk_forward_v1'
    return result


@lru_cache(maxsize=4)
def walk_forward_model(month, signature):
    from app.services.machine_learning.historical_match_model import HistoricalMatchModel
    from app.services.machine_learning.temporal_training import fit_walk_forward
    return fit_walk_forward(HistoricalMatchModel(), month)
