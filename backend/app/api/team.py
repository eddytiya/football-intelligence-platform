from collections import defaultdict
from datetime import date, datetime, time, timedelta
import re
import unicodedata

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import or_
from sqlalchemy.orm import Session, joinedload, selectinload

from app.db.session import get_db
from app.models.competition import Competition
from app.models.competition_team import CompetitionTeam
from app.models.match import Match
from app.models.team import Team
from app.models.player import Player
from app.services.etl.api_football_squad_sync import APIFootballSquadSync
from app.services.club_honours import get_club_honours


router = APIRouter(prefix="/teams", tags=["Teams"])
FINISHED_STATUSES = {"FINISHED", "AWARDED"}


def _form(matches, team_id):
    form = []
    for match in matches:
        is_home = match.home_team_id == team_id
        scored = match.home_score if is_home else match.away_score
        conceded = match.away_score if is_home else match.home_score
        form.append("W" if scored > conceded else "L" if scored < conceded else "D")
    return form


def _match_payload(match):
    return {
        "id": match.id, "utc_date": match.utc_date, "status": match.status,
        "home_team_id": match.home_team_id, "away_team_id": match.away_team_id,
        "home_team": match.home_team.name, "home_crest": match.home_team.crest,
        "away_team": match.away_team.name, "away_crest": match.away_team.crest,
        "home_score": match.home_score, "away_score": match.away_score,
        "competition": match.competition.name if match.competition else None,
        "competition_id": match.competition_id, "match_week": match.match_week,
    }


def _recorded_match_datetime(match):
    """Use provider dates first, with a safe fallback for legacy CSV import IDs."""
    if match.utc_date:
        return match.utc_date
    if match.match_date:
        return datetime.combine(match.match_date, time.min)
    legacy_date = (match.api_id or "").rsplit("_", 1)[-1]
    try:
        return datetime.strptime(legacy_date, "%d/%m/%y")
    except ValueError:
        return None


def _team_identity_key(name):
    """Collapse provider suffixes so current and historical club records connect."""
    ascii_name = unicodedata.normalize("NFKD", name or "").encode("ascii", "ignore").decode("ascii").lower()
    tokens = re.findall(r"[a-z0-9]+", ascii_name)
    while tokens and tokens[0] in {"fc", "cf", "afc", "sc", "ac"}:
        tokens.pop(0)
    while tokens and tokens[-1] in {"fc", "cf", "afc", "sc", "ac"}:
        tokens.pop()
    key = " ".join(tokens)
    # football-data.co.uk historical CSVs use short names while the live
    # provider stores official club names. Keep this map deliberate and
    # conservative: it only joins unequivocal club aliases.
    aliases = {
        "ath madrid": "club atletico de madrid",
        "atletico madrid": "club atletico de madrid",
        "ath bilbao": "athletic club",
        "sociedad": "real sociedad de futbol",
        "espanol": "rcd espanyol de barcelona",
        "la coruna": "deportivo la coruna",
        "sp gijon": "real sporting de gijon",
        "man city": "manchester city",
        "man united": "manchester united",
        "man utd": "manchester united",
        "newcastle": "newcastle united",
        "west ham": "west ham united",
        "wolves": "wolverhampton wanderers",
        "tottenham": "tottenham hotspur",
        "leeds": "leeds united",
        "norwich": "norwich city",
        "leicester": "leicester city",
        "brighton": "brighton hove albion",
        "nottm forest": "nottingham forest",
        "sheffield united": "sheffield united",
        "sheffield weds": "sheffield wednesday",
        "qpr": "queens park rangers",
        "west brom": "west bromwich albion",
        "inter": "internazionale milano",
        "internazionale": "internazionale milano",
        "paris sg": "paris saint germain",
        "psg": "paris saint germain",
        "bayern munich": "bayern munchen",
        "dortmund": "borussia dortmund",
    }
    return aliases.get(key, key)


@router.get("")
def get_teams(
    q: str | None = Query(default=None, max_length=80),
    competition_id: int | None = Query(default=None),
    limit: int = Query(default=300, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
):
    """Search the locally tracked clubs and return directory-ready snapshots."""
    query = db.query(Team)
    if q:
        query = query.filter(Team.name.ilike(f"%{q.strip()}%"))
    if competition_id:
        query = query.join(CompetitionTeam, CompetitionTeam.team_id == Team.id).filter(
            CompetitionTeam.competition_id == competition_id,
        )
    teams = query.options(
        selectinload(Team.competition_teams).joinedload(CompetitionTeam.competition),
    ).order_by(Team.name).offset(offset).limit(limit).all()
    team_ids = [team.id for team in teams]
    team_id_set = set(team_ids)
    recent_by_team = defaultdict(list)
    next_by_team = {}
    if team_ids:
        recent_matches = db.query(Match).options(
            joinedload(Match.home_team), joinedload(Match.away_team),
        ).filter(
            or_(Match.home_team_id.in_(team_ids), Match.away_team_id.in_(team_ids)),
            Match.status.in_(FINISHED_STATUSES),
        ).order_by(Match.utc_date.desc()).all()
        for match in recent_matches:
            for team_id in (match.home_team_id, match.away_team_id):
                if team_id in team_id_set and len(recent_by_team[team_id]) < 5:
                    recent_by_team[team_id].append(match)
        upcoming_matches = db.query(Match).options(
            joinedload(Match.home_team), joinedload(Match.away_team), joinedload(Match.competition),
        ).filter(
            or_(Match.home_team_id.in_(team_ids), Match.away_team_id.in_(team_ids)), Match.status.in_(["SCHEDULED", "TIMED"]), Match.utc_date > datetime.utcnow(),
        ).order_by(Match.utc_date).all()
        for match in upcoming_matches:
            next_by_team.setdefault(match.home_team_id, match)
            next_by_team.setdefault(match.away_team_id, match)
    result = []
    for team in teams:
        competitions = sorted((link.competition for link in team.competition_teams if link.competition), key=lambda item: item.name)
        recent = recent_by_team[team.id]
        next_match = next_by_team.get(team.id)
        result.append({
            "id": team.id, "name": team.name, "short_name": team.short_name, "tla": team.tla,
            "crest": team.crest, "founded": team.founded, "venue": team.venue,
            "competitions": [{"id": item.id, "name": item.name} for item in competitions],
            "form": _form(recent, team.id),
            "next_match": _match_payload(next_match) if next_match else None,
            "honours": get_club_honours(team.name),
        })
    return result


@router.get("/compare")
def compare_teams(
    first_team_id: int = Query(..., ge=1),
    second_team_id: int = Query(..., ge=1),
    db: Session = Depends(get_db),
):
    """Return completed head-to-head meetings from the most recent decade."""
    if first_team_id == second_team_id:
        raise HTTPException(status_code=400, detail="Select two different teams")

    first_team = db.query(Team).filter(Team.id == first_team_id).first()
    second_team = db.query(Team).filter(Team.id == second_team_id).first()
    if first_team is None or second_team is None:
        raise HTTPException(status_code=404, detail="Team not found")

    first_key = _team_identity_key(first_team.name)
    second_key = _team_identity_key(second_team.name)
    aliases = db.query(Team).all()
    first_ids = [team.id for team in aliases if _team_identity_key(team.name) == first_key]
    second_ids = [team.id for team in aliases if _team_identity_key(team.name) == second_key]
    cutoff = datetime.combine(date.today() - timedelta(days=3652), time.min)
    candidate_meetings = db.query(Match).options(
        joinedload(Match.home_team), joinedload(Match.away_team), joinedload(Match.competition),
    ).filter(
        Match.status.in_(FINISHED_STATUSES),
        or_(
            (Match.home_team_id.in_(first_ids)) & (Match.away_team_id.in_(second_ids)),
            (Match.home_team_id.in_(second_ids)) & (Match.away_team_id.in_(first_ids)),
        ),
    ).all()
    meetings = [match for match in candidate_meetings if (_recorded_match_datetime(match) or datetime.min) >= cutoff]
    meetings.sort(key=lambda match: _recorded_match_datetime(match) or datetime.min, reverse=True)

    first_wins = second_wins = draws = first_goals = second_goals = 0
    for match in meetings:
        first_is_home = match.home_team_id in first_ids
        first_score = match.home_score if first_is_home else match.away_score
        second_score = match.away_score if first_is_home else match.home_score
        first_goals += first_score
        second_goals += second_score
        if first_score > second_score:
            first_wins += 1
        elif first_score < second_score:
            second_wins += 1
        else:
            draws += 1

    return {
        "period": "last decade",
        "meetings": len(meetings),
        "first_team_wins": first_wins,
        "second_team_wins": second_wins,
        "draws": draws,
        "first_team_goals": first_goals,
        "second_team_goals": second_goals,
        "recent_meetings": [{**_match_payload(match), "utc_date": _recorded_match_datetime(match)} for match in meetings[:5]],
    }


@router.post("/sync/squads")
def sync_player_squads(
    team_id: int | None = Query(default=None),
    limit: int = Query(default=30, ge=1, le=30),
    db: Session = Depends(get_db),
):
    """Run a conservative manual squad batch without exceeding the free limit."""
    return APIFootballSquadSync(db).run_batch(team_id=team_id, limit=limit)


@router.get("/{team_id}")
def get_team_profile(team_id: int, db: Session = Depends(get_db)):
    """Return the club profile, last five results, and next fixtures."""
    team = db.query(Team).filter(Team.id == team_id).first()
    if team is None:
        raise HTTPException(status_code=404, detail="Team not found")
    base_query = db.query(Match).options(
        joinedload(Match.home_team), joinedload(Match.away_team), joinedload(Match.competition),
    ).filter(or_(Match.home_team_id == team_id, Match.away_team_id == team_id))
    recent = base_query.filter(Match.status.in_(FINISHED_STATUSES)).order_by(Match.utc_date.desc()).limit(5).all()
    upcoming = base_query.filter(Match.status.in_(["SCHEDULED", "TIMED"]), Match.utc_date > datetime.utcnow()).order_by(Match.utc_date).limit(10).all()
    competitions = db.query(Competition.id, Competition.name, Competition.emblem).join(
        CompetitionTeam, CompetitionTeam.competition_id == Competition.id,
    ).filter(CompetitionTeam.team_id == team_id).order_by(Competition.name).all()
    goals_for = goals_against = wins = draws = losses = 0
    for match in recent:
        home = match.home_team_id == team_id
        scored = match.home_score if home else match.away_score
        conceded = match.away_score if home else match.home_score
        goals_for += scored; goals_against += conceded
        if scored > conceded: wins += 1
        elif scored < conceded: losses += 1
        else: draws += 1
    # API-Football squad records use negative IDs to avoid colliding with the
    # legacy provider. When a current squad has been synced, show that clean
    # provider-specific roster instead of mixing historical duplicate rows.
    current_squad = db.query(Player).filter(
        Player.team_id == team_id, Player.api_id < 0,
    ).order_by(Player.position, Player.name).all()
    players = current_squad or db.query(Player).filter(
        Player.team_id == team_id,
    ).order_by(Player.position, Player.name).all()
    def player_payload(player):
        age = player.age
        if player.date_of_birth:
            age = date.today().year - player.date_of_birth.year - ((date.today().month, date.today().day) < (player.date_of_birth.month, player.date_of_birth.day))
        return {
            "id": player.id, "name": player.name, "first_name": player.first_name,
            "last_name": player.last_name, "position": player.position or "Unknown",
            "nationality": player.nationality, "shirt_number": player.shirt_number,
            "date_of_birth": player.date_of_birth, "age": age,
        }
    return {
        "id": team.id, "name": team.name, "short_name": team.short_name, "tla": team.tla, "crest": team.crest,
        "founded": team.founded, "venue": team.venue, "website": team.website, "club_colors": team.club_colors,
        "competitions": [{"id": item.id, "name": item.name, "emblem": item.emblem} for item in competitions],
        "form": _form(recent, team_id),
        "form_summary": {"wins": wins, "draws": draws, "losses": losses, "goals_for": goals_for, "goals_against": goals_against},
        "recent_results": [_match_payload(match) for match in recent],
        "upcoming_fixtures": [_match_payload(match) for match in upcoming],
        "players": [player_payload(player) for player in players],
        "honours": get_club_honours(team.name),
    }
