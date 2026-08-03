"""API-Football squad importer with conservative, auditable team mapping."""

from __future__ import annotations

import re
import unicodedata
from datetime import datetime

from sqlalchemy.orm import Session
from sqlalchemy import func

from app.models.competition import Competition
from app.models.competition_team import CompetitionTeam
from app.models.external_id import ExternalID
from app.models.player import Player
from app.models.team import Team
from app.services.api_football import APIFootballClient
from app.utils.date_parser import parse_date


PROVIDER = "api-football"

# Squad data is deliberately limited to the competitions shown as the core
# product experience. This keeps the free API-Football allowance focused on
# the leagues and tournaments users can browse in the application.
SQUAD_SYNC_COMPETITION_CODES = {
    "PL",   # Premier League
    "PD",   # Primera Division / La Liga
    "FL1",  # Ligue 1
    "BL1",  # Bundesliga
    "SA",   # Serie A
    "WC",   # FIFA World Cup
    "EC",   # European Championship
}

# Explicit first-wave squads requested for the product. Provider IDs are
# verified API-Football team identifiers, so these imports need one squad
# request each rather than several name-search requests. This preserves the
# free plan allowance and prevents similarly named clubs being mixed up.
INITIAL_SQUAD_TEAM_PROVIDER_IDS = {
    45: 42, 51: 50, 52: 33, 50: 40, 47: 49, 55: 47, 46: 66,
    71: 529, 72: 541, 70: 530, 67: 157, 66: 165, 86: 194,
    80: 85, 76: 496, 75: 505, 148: 489, 77: 492, 150: 497,
    252: 26, 96: 9, 100: 2, 99: 1, 97: 10, 254: 6, 117: 21,
}


def normalize_team_name(value: str | None) -> str:
    value = unicodedata.normalize("NFKD", value or "").encode("ascii", "ignore").decode("ascii").lower()
    value = re.sub(r"\b(fc|cf|sc|ac|afc|ud|rcd|cd|club|football)\b", " ", value)
    return re.sub(r"[^a-z0-9]", "", value)


class APIFootballSquadSync:
    def __init__(self, db: Session):
        self.db = db
        self.client = APIFootballClient()

    def _team_mapping(self, team: Team) -> ExternalID | None:
        return self.db.query(ExternalID).filter(
            ExternalID.entity_type == "team", ExternalID.provider == PROVIDER,
            ExternalID.entity_id == team.id,
        ).first()

    def _resolve_provider_team(self, team: Team) -> int | None:
        mapping = self._team_mapping(team)
        if mapping:
            return int(mapping.external_id)
        search_terms = [team.name, team.short_name]
        search_terms.append(re.sub(r"^(?:FC|CF|SC|AC|AFC|RCD|CD)\s+", "", team.name or "", flags=re.IGNORECASE))
        candidates_by_id = {}
        for term in dict.fromkeys(item.strip() for item in search_terms if item and item.strip()):
            payload = self.client.get("/teams", {"search": term})
            for candidate in (payload or {}).get("response", []):
                provider_id = candidate.get("team", {}).get("id")
                if provider_id:
                    candidates_by_id[provider_id] = candidate
        candidates = list(candidates_by_id.values())
        local_name = normalize_team_name(team.name)
        exact = [item for item in candidates if normalize_team_name(item.get("team", {}).get("name")) == local_name]
        local_countries = {
            normalize_team_name(area)
            for (area,) in self.db.query(Competition.area_name).join(
                CompetitionTeam, CompetitionTeam.competition_id == Competition.id,
            ).filter(CompetitionTeam.team_id == team.id).all()
        }
        country_exact = [
            item for item in exact
            if normalize_team_name(item.get("team", {}).get("country")) in local_countries
        ]
        if country_exact:
            exact = country_exact
        # Only exact normalized equality is accepted automatically. Ambiguous
        # aliases are skipped rather than risking a squad assigned to a rival.
        if len(exact) != 1:
            return None
        provider_id = exact[0]["team"]["id"]
        collision = self.db.query(ExternalID).filter(
            ExternalID.entity_type == "team", ExternalID.provider == PROVIDER,
            ExternalID.external_id == str(provider_id),
        ).first()
        if collision and collision.entity_id != team.id:
            return None
        self.db.add(ExternalID(entity_type="team", provider=PROVIDER, entity_id=team.id, external_id=str(provider_id)))
        self.db.flush()
        return provider_id

    def _store_explicit_team_mapping(self, team: Team, provider_team_id: int) -> int | None:
        mapping = self._team_mapping(team)
        if mapping:
            return int(mapping.external_id) if int(mapping.external_id) == provider_team_id else None
        collision = self.db.query(ExternalID).filter(
            ExternalID.entity_type == "team", ExternalID.provider == PROVIDER,
            ExternalID.external_id == str(provider_team_id),
        ).first()
        if collision and collision.entity_id != team.id:
            return None
        self.db.add(ExternalID(
            entity_type="team", provider=PROVIDER, entity_id=team.id,
            external_id=str(provider_team_id),
        ))
        self.db.flush()
        return provider_team_id

    def sync_team(self, team: Team, provider_team_id: int | None = None) -> dict:
        provider_team_id = (
            self._store_explicit_team_mapping(team, provider_team_id)
            if provider_team_id is not None else self._resolve_provider_team(team)
        )
        if provider_team_id is None:
            self.db.rollback()
            return {"team": team.name, "status": "unmatched", "players": 0}
        payload = self.client.get("/players/squads", {"team": provider_team_id})
        response = (payload or {}).get("response", [])
        squad = response[0].get("players", []) if response and isinstance(response[0], dict) else []
        if not squad:
            self.db.commit()
            return {"team": team.name, "status": "no_squad_returned", "players": 0}

        external_player_ids = [str(item.get("id")) for item in squad if item.get("id")]
        mappings = {
            item.external_id: item for item in self.db.query(ExternalID).filter(
                ExternalID.entity_type == "player", ExternalID.provider == PROVIDER,
                ExternalID.external_id.in_(external_player_ids),
            ).all()
        }
        synced = 0
        for data in squad:
            external_id = data.get("id")
            if not external_id:
                continue
            mapping = mappings.get(str(external_id))
            player = self.db.query(Player).filter(Player.id == mapping.entity_id).first() if mapping else None
            if player is None:
                # Negative IDs isolate API-Football IDs from football-data.org's
                # required positive player.api_id namespace.
                player = Player(api_id=-int(external_id), team_id=team.id, name=data.get("name") or "Unknown Player")
                self.db.add(player)
                self.db.flush()
                mapping = ExternalID(entity_type="player", provider=PROVIDER, entity_id=player.id, external_id=str(external_id))
                self.db.add(mapping)
                mappings[str(external_id)] = mapping
            player.team_id = team.id
            player.name = data.get("name") or player.name
            player.first_name = data.get("firstname") or data.get("firstName") or player.first_name
            player.last_name = data.get("lastname") or data.get("lastName") or player.last_name
            birth = data.get("birth") or {}
            player.date_of_birth = parse_date(birth.get("date")) or player.date_of_birth
            player.age = data.get("age") or player.age
            player.nationality = data.get("nationality") or player.nationality
            player.position = data.get("position") or player.position
            player.shirt_number = data.get("number") or player.shirt_number
            player.last_updated = datetime.utcnow().isoformat()
            synced += 1
        self.db.commit()
        return {"team": team.name, "status": "synced", "players": synced}

    def run_batch(self, team_id: int | None = None, limit: int = 30) -> dict:
        # A club can appear in several competitions (for example Barcelona in
        # La Liga and the Champions League). DISTINCT guarantees its squad is
        # fetched only once per batch.
        query = self.db.query(Team).join(
            CompetitionTeam, CompetitionTeam.team_id == Team.id,
        ).join(
            Competition, Competition.id == CompetitionTeam.competition_id,
        ).filter(
            Team.api_id.isnot(None),
            Competition.code.in_(SQUAD_SYNC_COMPETITION_CODES),
        ).distinct()
        if team_id is not None:
            query = query.filter(Team.id == team_id)
            teams = query.order_by(Team.id).limit(1).all()
        else:
            mapped_ids = {
                item.entity_id for item in self.db.query(ExternalID.entity_id).filter(
                    ExternalID.entity_type == "team", ExternalID.provider == PROVIDER,
                ).all()
            }
            # First map clubs that have never been imported. Once coverage is
            # complete, rotate through the oldest squad refreshes so a newly
            # registered player is picked up in a later 26-hour cycle.
            all_teams = query.all()
            unmapped = sorted((item for item in all_teams if item.id not in mapped_ids), key=lambda item: item.id)
            remaining_slots = max(0, min(limit, 30) - len(unmapped))
            if remaining_slots:
                refreshed_at = dict(self.db.query(
                    Player.team_id, func.max(Player.last_updated),
                ).filter(Player.api_id < 0).group_by(Player.team_id).all())
                mapped = sorted(
                    (item for item in all_teams if item.id in mapped_ids),
                    key=lambda item: (refreshed_at.get(item.id) is not None, refreshed_at.get(item.id) or "", item.id),
                )
                teams = unmapped[:min(limit, 30)] + mapped[:remaining_slots]
            else:
                teams = unmapped[:min(limit, 30)]
        report = {"processed": 0, "synced": 0, "players": 0, "unmatched": 0, "no_squad": 0}
        for index, team in enumerate(teams):
            result = self.sync_team(team)
            report["processed"] += 1
            report["players"] += result["players"]
            if result["status"] == "synced": report["synced"] += 1
            elif result["status"] == "unmatched": report["unmatched"] += 1
            else: report["no_squad"] += 1
            if index < len(teams) - 1:
                self.client.pause_for_free_tier()
        return report

    def run_initial_selected_batch(self) -> dict:
        """Sync only the user-selected first wave with one API call per squad."""
        teams = self.db.query(Team).filter(Team.id.in_(INITIAL_SQUAD_TEAM_PROVIDER_IDS)).all()
        by_id = {team.id: team for team in teams}
        report = {"requested": len(INITIAL_SQUAD_TEAM_PROVIDER_IDS), "processed": 0, "synced": 0, "players": 0, "unmatched": 0, "no_squad": 0}
        for index, team_id in enumerate(INITIAL_SQUAD_TEAM_PROVIDER_IDS):
            team = by_id.get(team_id)
            if team is None:
                report["unmatched"] += 1
                continue
            result = self.sync_team(team, INITIAL_SQUAD_TEAM_PROVIDER_IDS[team_id])
            report["processed"] += 1
            report["players"] += result["players"]
            if result["status"] == "synced": report["synced"] += 1
            elif result["status"] == "unmatched": report["unmatched"] += 1
            else: report["no_squad"] += 1
            if index < len(INITIAL_SQUAD_TEAM_PROVIDER_IDS) - 1:
                self.client.pause_for_free_tier()
        return report
