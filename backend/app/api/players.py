from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session, joinedload

from app.db.session import get_db
from app.models.competition_team import CompetitionTeam
from app.models.player import Player
from app.models.team import Team


router = APIRouter(prefix="/players", tags=["Players"])


def _player_payload(player: Player) -> dict:
    return {
        "id": player.id,
        "name": player.name,
        "position": player.position,
        "nationality": player.nationality,
        "age": player.age,
        "shirt_number": player.shirt_number,
        "team_id": player.team_id,
        "team_name": player.team.name if player.team else None,
        "team_crest": player.team.crest if player.team else None,
    }


@router.get("")
def get_players(
    q: str | None = Query(default=None, max_length=100),
    competition_id: int | None = Query(default=None),
    position: str | None = Query(default=None),
    limit: int = Query(default=60, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
):
    """Search the locally stored player directory across every tracked club."""

    query = db.query(Player).options(joinedload(Player.team))
    if q:
        query = query.filter(Player.name.ilike(f"%{q.strip()}%"))
    if position:
        query = query.filter(Player.position == position)
    if competition_id:
        query = query.join(Team, Team.id == Player.team_id).join(
            CompetitionTeam, CompetitionTeam.team_id == Team.id,
        ).filter(CompetitionTeam.competition_id == competition_id)

    players = query.order_by(Player.name).offset(offset).limit(limit).all()
    return [_player_payload(player) for player in players]


@router.get("/positions")
def get_player_positions(db: Session = Depends(get_db)):
    """Return the real, distinct position labels stored in the database."""

    rows = db.query(Player.position).filter(Player.position.isnot(None)).distinct().all()
    return sorted({row[0] for row in rows if row[0]})
