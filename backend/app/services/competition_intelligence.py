"""Competition-level analytics built from locally synced match results.

The calculations deliberately use only data already in the project database, so
the dashboard keeps working when the external provider is unavailable.
"""

from __future__ import annotations

from collections import defaultdict
from datetime import datetime
from math import exp, factorial
from random import Random
import re

from sqlalchemy.orm import Session

from app.models.match import Match
from app.models.competition_team import CompetitionTeam
from app.models.player import Player
from app.models.player_season_scorer import PlayerSeasonScorer
from app.models.season import Season


FINISHED_STATUSES = {"FINISHED", "AWARDED"}


class CompetitionIntelligenceService:
    def __init__(self, db: Session):
        self.db = db

    @staticmethod
    def _poisson(lam: float, goals: int) -> float:
        return exp(-lam) * (lam ** goals) / factorial(goals)

    def _probabilities(self, home, away, strengths):
        league_goal_rate = strengths["league_goal_rate"]
        home_attack = strengths[home]["attack"]
        home_defence = strengths[home]["defence"]
        away_attack = strengths[away]["attack"]
        away_defence = strengths[away]["defence"]
        home_xg = max(.25, min(3.7, league_goal_rate * home_attack * away_defence * 1.10))
        away_xg = max(.20, min(3.4, league_goal_rate * away_attack * home_defence * .92))
        home_win = draw = away_win = 0.0
        for home_goals in range(8):
            for away_goals in range(8):
                probability = self._poisson(home_xg, home_goals) * self._poisson(away_xg, away_goals)
                if home_goals > away_goals:
                    home_win += probability
                elif home_goals < away_goals:
                    away_win += probability
                else:
                    draw += probability
        total = home_win + draw + away_win
        return home_xg, away_xg, home_win / total, draw / total, away_win / total

    @staticmethod
    def _result(home_goals: int, away_goals: int):
        if home_goals > away_goals:
            return "W", "L"
        if home_goals < away_goals:
            return "L", "W"
        return "D", "D"

    def _historical_strength_priors(self, competition_id: int, current_season: Season, current_teams: dict, history_seasons: int = 5):
        """Build pre-season attack/defence priors from recent completed seasons.

        A new season has no completed matches, so relying on its current table
        would make every club look identical.  This uses the same weighted,
        provider-safe club matching as the season-outlook feature until enough
        current-season evidence exists.
        """
        previous = self.db.query(Season).filter(
            Season.competition_id == competition_id,
            Season.id != current_season.id,
            Season.end_year <= current_season.start_year,
        ).order_by(Season.end_year.desc(), Season.id.desc()).limit(history_seasons).all()

        prior_rows = defaultdict(lambda: {"attack": 0.0, "defence": 0.0, "ppg": 0.0, "weight": 0.0, "seasons": []})
        weighted_goal_rate = 0.0
        goal_rate_weight = 0.0

        for index, season in enumerate(previous):
            completed = self.db.query(Match).filter(
                Match.competition_id == competition_id,
                Match.season_id == season.id,
                Match.status.in_(FINISHED_STATUSES),
                Match.home_score.isnot(None),
                Match.away_score.isnot(None),
            ).all()
            if not completed:
                continue
            table = self._season_table(completed)
            league_games = sum(row["played"] for row in table.values())
            league_goal_rate = sum(row["goals_for"] for row in table.values()) / max(1, league_games)
            weight = history_seasons - index
            weighted_goal_rate += league_goal_rate * weight
            goal_rate_weight += weight
            table_by_name = {self._team_key(row["team"].name): row for row in table.values()}

            for team_id, team in current_teams.items():
                row = table.get(team_id) or table_by_name.get(self._team_key(team.name))
                if not row or not row["played"]:
                    continue
                item = prior_rows[team_id]
                item["attack"] += (row["goals_for"] / row["played"] / max(.25, league_goal_rate)) * weight
                item["defence"] += (row["goals_against"] / row["played"] / max(.25, league_goal_rate)) * weight
                item["ppg"] += (row["points"] / row["played"]) * weight
                item["weight"] += weight
                item["seasons"].append(season.season_name)

        priors = {}
        for team_id in current_teams:
            item = prior_rows[team_id]
            if item["weight"]:
                priors[team_id] = {
                    "attack": max(.55, min(1.7, item["attack"] / item["weight"])),
                    "defence": max(.55, min(1.7, item["defence"] / item["weight"])),
                    "ppg": item["ppg"] / item["weight"],
                    "seasons": item["seasons"],
                }
            else:
                priors[team_id] = {"attack": 1.0, "defence": 1.0, "ppg": 1.35, "seasons": []}
        return priors, (weighted_goal_rate / goal_rate_weight if goal_rate_weight else 1.35), [season.season_name for season in previous]

    def get_intelligence(self, competition_id: int, simulations: int = 1500) -> dict:
        season = self.db.query(Season).filter(Season.competition_id == competition_id).order_by(
            Season.end_year.desc(), Season.id.desc(),
        ).first()
        if season is None:
            return {"season": None, "data_coverage": 0, "table": [], "upsets": []}

        matches = self.db.query(Match).filter(
            Match.competition_id == competition_id,
            Match.season_id == season.id,
        ).all()
        teams = {}
        for match in matches:
            if match.home_team:
                teams[match.home_team_id] = match.home_team
            if match.away_team:
                teams[match.away_team_id] = match.away_team

        stats = {
            team_id: {"played": 0, "won": 0, "draw": 0, "lost": 0, "points": 0, "gf": 0, "ga": 0, "form": [], "timeline": [], "home": {"played": 0, "points": 0, "won": 0}, "away": {"played": 0, "points": 0, "won": 0}}
            for team_id in teams
        }
        completed = [match for match in matches if match.status in FINISHED_STATUSES and match.home_score is not None and match.away_score is not None]
        for match in completed:
            home, away = stats[match.home_team_id], stats[match.away_team_id]
            home["played"] += 1; away["played"] += 1; home["home"]["played"] += 1; away["away"]["played"] += 1
            home["gf"] += match.home_score; home["ga"] += match.away_score
            away["gf"] += match.away_score; away["ga"] += match.home_score
            home_result, away_result = self._result(match.home_score, match.away_score)
            if home_result == "W": home["won"] += 1; away["lost"] += 1; home["points"] += 3; home["home"]["won"] += 1; home["home"]["points"] += 3
            elif home_result == "L": away["won"] += 1; home["lost"] += 1; away["points"] += 3; away["away"]["won"] += 1; away["away"]["points"] += 3
            else: home["draw"] += 1; away["draw"] += 1; home["points"] += 1; away["points"] += 1; home["home"]["points"] += 1; away["away"]["points"] += 1

        for match in sorted(completed, key=lambda item: item.utc_date or datetime.min, reverse=True):
            home_result, away_result = self._result(match.home_score, match.away_score)
            if len(stats[match.home_team_id]["form"]) < 10: stats[match.home_team_id]["form"].append(home_result)
            if len(stats[match.away_team_id]["form"]) < 10: stats[match.away_team_id]["form"].append(away_result)

        for index, match in enumerate(sorted(completed, key=lambda item: item.utc_date or datetime.min), start=1):
            home_result, away_result = self._result(match.home_score, match.away_score)
            week = match.match_week or index
            stats[match.home_team_id]["timeline"].append({"week": week, "result": home_result})
            stats[match.away_team_id]["timeline"].append({"week": week, "result": away_result})

        total_goals = sum(item["gf"] for item in stats.values())
        completed_games = sum(item["played"] for item in stats.values()) // 2
        priors, historical_goal_rate, prior_seasons = self._historical_strength_priors(competition_id, season, teams)
        base_goal_rate = max(.8, total_goals / (completed_games * 2)) if completed_games else historical_goal_rate
        strengths = {"league_goal_rate": base_goal_rate}
        for team_id, item in stats.items():
            games = item["played"]
            # Current form becomes decisive after roughly eight matches; before
            # then recent-season performance prevents an empty table from
            # assigning the same strength to every club.
            current_attack = ((item["gf"] / games) * games + base_goal_rate * 5) / (games + 5) / base_goal_rate if games else 1.0
            current_defence = ((item["ga"] / games) * games + base_goal_rate * 5) / (games + 5) / base_goal_rate if games else 1.0
            current_weight = min(1.0, games / 8)
            prior = priors[team_id]
            strengths[team_id] = {
                "attack": current_attack * current_weight + prior["attack"] * (1 - current_weight),
                "defence": current_defence * current_weight + prior["defence"] * (1 - current_weight),
            }

        scheduled = [match for match in matches if match.status == "SCHEDULED"]
        fixture_probabilities = [
            (match, *self._probabilities(match.home_team_id, match.away_team_id, strengths))
            for match in scheduled
        ]
        fixture_difficulty = defaultdict(list)
        for match in sorted(scheduled, key=lambda item: item.utc_date or datetime.max):
            for team_id, opponent_id, is_away in ((match.home_team_id, match.away_team_id, False), (match.away_team_id, match.home_team_id, True)):
                opponent = strengths[opponent_id]
                rating = opponent["attack"] + (2 - opponent["defence"])
                difficulty = max(1, min(5, round(2.5 + (rating - 2) * 1.25 + (.35 if is_away else 0))))
                if len(fixture_difficulty[team_id]) < 5:
                    fixture_difficulty[team_id].append({"opponent": teams[opponent_id].name, "away": is_away, "difficulty": difficulty, "week": match.match_week})
        # Use a fixed seed so that refreshing the page does not make probabilities jump.
        random = Random(f"{competition_id}-{season.id}-{len(completed)}")
        simulated_points = defaultdict(list)
        simulated_positions = defaultdict(list)
        simulations = max(300, min(simulations, 3000))
        for _ in range(simulations):
            points = {team_id: item["points"] for team_id, item in stats.items()}
            goal_difference = {team_id: item["gf"] - item["ga"] for team_id, item in stats.items()}
            for match, _, _, home_win, draw, _ in fixture_probabilities:
                roll = random.random()
                if roll < home_win:
                    points[match.home_team_id] += 3; goal_difference[match.home_team_id] += 1
                    goal_difference[match.away_team_id] -= 1
                elif roll < home_win + draw:
                    points[match.home_team_id] += 1; points[match.away_team_id] += 1
                else:
                    points[match.away_team_id] += 3; goal_difference[match.home_team_id] -= 1
                    goal_difference[match.away_team_id] += 1
            ranking = sorted(teams, key=lambda team_id: (-points[team_id], -goal_difference[team_id], teams[team_id].name))
            for position, team_id in enumerate(ranking, 1):
                simulated_points[team_id].append(points[team_id])
                simulated_positions[team_id].append(position)

        rows = []
        team_count = len(teams)
        relegation_positions = max(3, team_count // 6)
        for team_id, team in teams.items():
            item = stats[team_id]
            form = item["form"][:5]
            recent_points = sum({"W": 3, "D": 1, "L": 0}[result] for result in form)
            prior = item["form"][5:10]
            prior_points = sum({"W": 3, "D": 1, "L": 0}[result] for result in prior)
            trend = "Stable" if len(prior) < 3 or abs(recent_points - prior_points) <= 1 else ("Improving" if recent_points > prior_points else "Declining")
            positions = simulated_positions[team_id]
            rows.append({
                "team": team.name, "crest": team.crest, "played": item["played"], "points": item["points"],
                "goal_difference": item["gf"] - item["ga"], "goals_for": item["gf"], "goals_against": item["ga"],
                "form": form, "form_trend": trend, "attack_rating": round(strengths[team_id]["attack"], 2),
                "defence_rating": round(strengths[team_id]["defence"], 2),
                "historical_ppg": round(priors[team_id]["ppg"], 2),
                "historical_seasons": priors[team_id]["seasons"],
                "expected_points": round(sum(simulated_points[team_id]) / simulations, 1),
                "expected_position": round(sum(positions) / simulations, 1),
                "rank_range": [min(positions), max(positions)],
                "title_probability": round(100 * sum(position == 1 for position in positions) / simulations, 1),
                "top_four_probability": round(100 * sum(position <= min(4, team_count) for position in positions) / simulations, 1),
                "relegation_probability": round(100 * sum(position > team_count - relegation_positions for position in positions) / simulations, 1),
                "home_record": item["home"], "away_record": item["away"],
                "fixture_difficulty": fixture_difficulty[team_id], "form_timeline": item["timeline"][-10:],
            })
        # Before the first result, the useful table is the projected one rather
        # than an alphabetical list of 0-point teams.
        if completed:
            rows.sort(key=lambda item: (-item["points"], -item["goal_difference"], item["team"]))
        else:
            rows.sort(key=lambda item: (item["expected_position"], -item["expected_points"], item["team"]))

        upsets = []
        for match, home_xg, away_xg, home_win, draw, away_win in fixture_probabilities[:80]:
            home_points, away_points = stats[match.home_team_id]["points"], stats[match.away_team_id]["points"]
            underdog_id = match.home_team_id if home_points < away_points else match.away_team_id
            underdog_chance = home_win if underdog_id == match.home_team_id else away_win
            if underdog_chance >= .25 and home_points != away_points:
                upsets.append({"id": match.id, "home_team": teams[match.home_team_id].name, "away_team": teams[match.away_team_id].name, "utc_date": match.utc_date, "underdog": teams[underdog_id].name, "underdog_probability": round(underdog_chance * 100, 1), "expected_goals": [round(home_xg, 2), round(away_xg, 2)]})
        upsets.sort(key=lambda item: item["underdog_probability"], reverse=True)
        return {
            "season": season.season_name,
            "data_coverage": len(completed),
            "simulations": simulations,
            "table": rows,
            "upsets": upsets[:5],
            "historical_prior_seasons": prior_seasons,
            "strength_basis": "Current-season results" if completed else "Weighted recent completed seasons",
        }

    @staticmethod
    def _season_table(matches):
        """Build a final table from stored completed matches for one season."""
        table = {}
        for match in matches:
            if match.home_team_id not in table:
                table[match.home_team_id] = {"team": match.home_team, "played": 0, "won": 0, "draw": 0, "lost": 0, "points": 0, "goals_for": 0, "goals_against": 0}
            if match.away_team_id not in table:
                table[match.away_team_id] = {"team": match.away_team, "played": 0, "won": 0, "draw": 0, "lost": 0, "points": 0, "goals_for": 0, "goals_against": 0}
            home, away = table[match.home_team_id], table[match.away_team_id]
            home["played"] += 1; away["played"] += 1
            home["goals_for"] += match.home_score; home["goals_against"] += match.away_score
            away["goals_for"] += match.away_score; away["goals_against"] += match.home_score
            if match.home_score > match.away_score:
                home["won"] += 1; away["lost"] += 1; home["points"] += 3
            elif match.home_score < match.away_score:
                away["won"] += 1; home["lost"] += 1; away["points"] += 3
            else:
                home["draw"] += 1; away["draw"] += 1; home["points"] += 1; away["points"] += 1
        ranked = sorted(table.items(), key=lambda item: (-item[1]["points"], -(item[1]["goals_for"] - item[1]["goals_against"]), item[1]["team"].name))
        return {team_id: {**entry, "position": index} for index, (team_id, entry) in enumerate(ranked, 1)}

    @staticmethod
    def _team_key(name: str) -> str:
        """Provider-safe name key for linking historical CSV clubs to live provider clubs."""
        normalized = re.sub(r"[^a-z0-9 ]", " ", (name or "").lower())
        tokens = [token for token in normalized.split() if token not in {"fc", "afc", "cf", "ac", "club", "the"}]
        value = " ".join(tokens)
        aliases = {
            "tottenham hotspur": "tottenham", "brighton hove albion": "brighton",
            "wolverhampton wanderers": "wolves", "west bromwich albion": "west brom",
            "queens park rangers": "qpr", "nottingham forest": "nottingham forest",
            "man city": "manchester city", "man utd": "manchester united",
        }
        return aliases.get(value, value)

    def get_season_outlook(self, competition_id: int, history_seasons: int = 5) -> dict:
        """Forecast the current scheduled season with recent multi-season league performance."""
        current = self.db.query(Season).filter(Season.competition_id == competition_id).order_by(Season.end_year.desc(), Season.id.desc()).first()
        if current is None:
            return {"season": None, "forecast": [], "history": [], "top_scorer_candidates": [], "message": "No season data is stored for this competition."}

        current_matches = self.db.query(Match).filter(Match.competition_id == competition_id, Match.season_id == current.id).all()
        current_teams = {}
        for match in current_matches:
            current_teams[match.home_team_id] = match.home_team
            current_teams[match.away_team_id] = match.away_team
        previous = self.db.query(Season).filter(Season.competition_id == competition_id, Season.id != current.id, Season.end_year <= current.start_year).order_by(Season.end_year.desc()).limit(history_seasons).all()
        season_tables = []
        for season in previous:
            completed = self.db.query(Match).filter(Match.competition_id == competition_id, Match.season_id == season.id, Match.status.in_(FINISHED_STATUSES), Match.home_score.isnot(None), Match.away_score.isnot(None)).all()
            if completed:
                season_tables.append((season, self._season_table(completed)))

        league_ppg = []
        for _, table in season_tables:
            league_ppg.extend(row["points"] / row["played"] for row in table.values() if row["played"])
        baseline_ppg = sum(league_ppg) / len(league_ppg) if league_ppg else 1.35
        current_completed = [match for match in current_matches if match.status in FINISHED_STATUSES and match.home_score is not None and match.away_score is not None]
        current_table = self._season_table(current_completed) if current_completed else {}
        history = []
        forecasts = []
        for team_id, team in current_teams.items():
            records = []
            weighted_ppg = weighted_gd = weight_total = 0.0
            for index, (season, table) in enumerate(season_tables):
                row = table.get(team_id)
                if row is None:
                    key = self._team_key(team.name)
                    row = next((candidate for candidate in table.values() if self._team_key(candidate["team"].name) == key), None)
                if not row:
                    continue
                weight = history_seasons - index
                ppg = row["points"] / max(1, row["played"])
                gdpg = (row["goals_for"] - row["goals_against"]) / max(1, row["played"])
                weighted_ppg += ppg * weight; weighted_gd += gdpg * weight; weight_total += weight
                records.append({"season": season.season_name, "position": row["position"], "played": row["played"], "won": row["won"], "draw": row["draw"], "lost": row["lost"], "points": row["points"], "goals_for": row["goals_for"], "goals_against": row["goals_against"]})
            historical_ppg = weighted_ppg / weight_total if weight_total else baseline_ppg
            historical_gd = weighted_gd / weight_total if weight_total else 0
            scheduled_games = sum(1 for match in current_matches if match.status == "SCHEDULED" and team_id in (match.home_team_id, match.away_team_id))
            current_row = current_table.get(team_id)
            current_points = current_row["points"] if current_row else 0
            current_played = current_row["played"] if current_row else 0
            remaining = scheduled_games
            form_adjustment = min(.18, max(-.18, historical_gd * .08))
            projected_points = current_points + max(.6, historical_ppg + form_adjustment) * remaining
            forecasts.append({"team": team.name, "crest": team.crest, "projected_points": round(projected_points, 1), "historical_ppg": round(historical_ppg, 2), "current_points": current_points, "current_played": current_played, "remaining_fixtures": remaining, "history_count": len(records)})
            history.append({"team": team.name, "crest": team.crest, "seasons": records})
        forecasts.sort(key=lambda row: (-row["projected_points"], -row["historical_ppg"], row["team"]))
        for position, row in enumerate(forecasts, 1):
            row["projected_position"] = position

        # A candidate must be both a stored historical scorer and in the current local squad pool.
        active_players = self.db.query(Player.name, Player.team_id).join(CompetitionTeam, CompetitionTeam.team_id == Player.team_id).filter(CompetitionTeam.competition_id == competition_id, Player.api_id < 0).all()
        active_by_name = {" ".join(name.lower().split()): team_id for name, team_id in active_players}
        scorer_rows = self.db.query(PlayerSeasonScorer).filter(PlayerSeasonScorer.competition_id == competition_id, PlayerSeasonScorer.goals > 0).all()
        candidates = {}
        for scorer in scorer_rows:
            key = " ".join(scorer.player_name.lower().split())
            team_id = active_by_name.get(key)
            if not team_id:
                continue
            item = candidates.setdefault(key, {"player": scorer.player_name, "team_id": team_id, "goals": 0, "appearances": 0, "seasons": set()})
            item["goals"] += scorer.goals; item["appearances"] += scorer.appearances; item["seasons"].add(scorer.season_year)
        team_names = {team_id: team.name for team_id, team in current_teams.items()}
        top_scorer_candidates = []
        for item in candidates.values():
            seasons = max(1, len(item["seasons"]))
            top_scorer_candidates.append({"player": item["player"], "club": team_names.get(item["team_id"], "Current club"), "projected_goals": round(item["goals"] / seasons, 1), "historical_goals": item["goals"], "seasons": sorted(item["seasons"])})
        top_scorer_candidates.sort(key=lambda row: (-row["projected_goals"], -row["historical_goals"], row["player"]))
        return {"season": current.season_name, "forecast": forecasts, "history": history, "top_scorer_candidates": top_scorer_candidates[:10], "historical_seasons_used": [season.season_name for season, _ in season_tables], "message": None if season_tables else "No completed historical seasons are available for this competition."}
