from collections import Counter
from datetime import date, datetime, timedelta
from app.models.match import Match
from sqlalchemy import func
from sqlalchemy.orm import Session, joinedload

from app.models.competition import Competition
from app.models.player import Player
from app.models.prediction import Prediction
from app.models.prediction_evaluation import PredictionEvaluation


class DashboardRepository:
    """
    Repository responsible for dashboard queries.
    """

    def __init__(self, db: Session):
        self.db = db

    def get_summary_statistics(self):
        """
        Get summary statistics for the dashboard.
        """

        total_predictions = (
            self.db.query(Prediction)
            .count()
        )

        correct_predictions = (
            self.db.query(PredictionEvaluation)
            .filter(PredictionEvaluation.correct.is_(True))
            .count()
        )

        incorrect_predictions = (
            self.db.query(PredictionEvaluation)
            .filter(PredictionEvaluation.correct.is_(False))
            .count()
        )

        today_predictions = (
            self.db.query(Prediction)
            .filter(
                func.date(Prediction.predicted_at) == date.today()
            )
            .count()
        )

        accuracy = 0.0

        if total_predictions > 0:
            accuracy = round(
                (correct_predictions / total_predictions) * 100,
                2,
            )

        return {
            "total_predictions": total_predictions,
            "correct_predictions": correct_predictions,
            "incorrect_predictions": incorrect_predictions,
            "today_predictions": today_predictions,
            "accuracy": accuracy,
        }

    def get_recent_predictions(self, limit: int = 10):
        """
        Returns the most recent predictions.
        """

        rows = (
            self.db.query(
                Prediction.id,
                Prediction.prediction,
                Prediction.home_probability,
                Prediction.draw_probability,
                Prediction.away_probability,
                Prediction.predicted_at,
                PredictionEvaluation.actual_result,
                PredictionEvaluation.correct,
            )
            .outerjoin(
                PredictionEvaluation,
                Prediction.id == PredictionEvaluation.prediction_id,
            )
            .order_by(Prediction.predicted_at.desc())
            .limit(limit)
            .all()
        )

        predictions = []

        for row in rows:

            confidence = max(
                row.home_probability,
                row.draw_probability,
                row.away_probability,
            )

            predictions.append(
                {
                    "match": f"Prediction #{row.id}",
                    "prediction": row.prediction,
                    "actual_result": row.actual_result,
                    "correct": row.correct,
                    "confidence": round(confidence * 100, 2),
                }
            )

        return predictions

    def get_upcoming_matches(self, limit: int = 10):
        """
        Returns upcoming scheduled matches.
        """

        rows = (
            self.db.query(Match)
            .filter(
                Match.status.in_(
                    [
                        "SCHEDULED",
                        "TIMED",
                    ]
                )
            )
            .order_by(Match.utc_date.asc())
            .limit(limit)
            .all()
        )

        matches = []

        for match in rows:
            matches.append(
                {
                    "home_team": match.home_team.name,
                    "away_team": match.away_team.name,
                    "competition": match.competition.name,
                    "utc_date": match.utc_date,
                }
            )

        return matches

    def get_model_performance(self):
        """
        Returns model performance statistics.
        """

        total_predictions = (
            self.db.query(Prediction)
            .count()
        )

        correct_predictions = (
            self.db.query(PredictionEvaluation)
            .filter(
                PredictionEvaluation.correct.is_(True)
            )
            .count()
        )

        accuracy = 0.0

        if total_predictions > 0:
            accuracy = round(
                (correct_predictions / total_predictions) * 100,
                2,
            )

        return {
            "accuracy": accuracy,
            "total_predictions": total_predictions,
        }

    @staticmethod
    def _match_payload(match):
        return {
            "id": match.id,
            "home_team_id": match.home_team_id,
            "away_team_id": match.away_team_id,
            "home_team": match.home_team.name,
            "away_team": match.away_team.name,
            "home_crest": match.home_team.crest,
            "away_crest": match.away_team.crest,
            "competition": match.competition.name,
            "competition_id": match.competition_id,
            "utc_date": match.utc_date,
            "status": match.status,
            "match_week": match.match_week,
            "home_score": match.home_score,
            "away_score": match.away_score,
        }

    def get_command_centre(self):
        """A live, data-only home-board. No demo teams or invented metrics."""
        now = datetime.utcnow()
        base = self.db.query(Match).options(
            joinedload(Match.home_team), joinedload(Match.away_team), joinedload(Match.competition),
        )
        live_statuses = {"IN_PLAY", "PAUSED", "LIVE", "FIRST_HALF", "SECOND_HALF", "HALFTIME"}
        # Do not allow an unsynchronised old SCHEDULED row to masquerade as
        # today's football. A fixture remains eligible for live display only
        # around its kick-off window, while upcoming fixtures must be future.
        live = base.filter(
            Match.status.in_(live_statuses),
            Match.utc_date >= now - timedelta(hours=6),
        ).order_by(Match.utc_date.asc()).limit(6).all()
        scheduled = base.filter(
            Match.status.in_({"SCHEDULED", "TIMED"}),
            Match.utc_date >= now,
        ).order_by(Match.utc_date.asc()).limit(24).all()
        finished = base.filter(Match.status.in_({"FINISHED", "AWARDED"})).order_by(Match.utc_date.desc()).limit(8).all()
        featured = live[0] if live else (scheduled[0] if scheduled else None)

        # Attach a saved pre-kick-off forecast where one exists. The dashboard
        # deliberately presents forecast vs final score, not an accuracy rate.
        prediction_rows = self.db.query(Prediction).filter(
            Prediction.match_id.in_([match.id for match in finished]) if finished else False,
        ).order_by(Prediction.predicted_at.desc()).all() if finished else []
        predictions = {}
        for prediction in prediction_rows:
            predictions.setdefault(prediction.match_id, prediction)
        timeline = []
        for match in finished[:5]:
            prediction = predictions.get(match.id)
            timeline.append({
                **self._match_payload(match),
                "forecast": prediction.prediction if prediction else None,
                "final_score": f"{match.home_score}–{match.away_score}",
            })

        next_two_weeks = [match for match in scheduled if match.utc_date and match.utc_date <= now + timedelta(days=14)]
        congestion = Counter(team_id for match in next_two_weeks for team_id in (match.home_team_id, match.away_team_id))
        congested_team_id, congested_count = congestion.most_common(1)[0] if congestion else (None, 0)
        congested_team = None
        if congested_team_id:
            match = next(item for item in next_two_weeks if congested_team_id in (item.home_team_id, item.away_team_id))
            congested_team = match.home_team if match.home_team_id == congested_team_id else match.away_team

        premier_league = self.db.query(Competition).filter(Competition.name == "Premier League").first()
        race = []
        race_basis = None
        if premier_league:
            # Local import avoids a dependency cycle at module import time.
            from app.services.competition_intelligence import CompetitionIntelligenceService
            intelligence = CompetitionIntelligenceService(self.db).get_intelligence(premier_league.id, simulations=500)
            race = intelligence.get("table", [])[:4]
            race_basis = intelligence.get("strength_basis")

        squad_teams = self.db.query(Player.team_id).filter(Player.api_id < 0).distinct().count()
        squad_players = self.db.query(Player).filter(Player.api_id < 0).count()
        latest_squad_update = self.db.query(func.max(Player.last_updated)).filter(Player.api_id < 0).scalar()
        return {
            "generated_at": now,
            "featured": self._match_payload(featured) if featured else None,
            "live_matches": [self._match_payload(match) for match in live],
            "upcoming": [self._match_payload(match) for match in scheduled[:10]],
            "timeline": timeline,
            "league_race": race,
            "league_race_basis": race_basis,
            "insights": {
                "featured_label": "Live now" if live else "Next featured fixture",
                "fixture_congestion": {
                    "team": congested_team.name if congested_team else None,
                    "crest": congested_team.crest if congested_team else None,
                    "matches": congested_count,
                    "period": "next 14 days",
                },
                "next_fixture_count": len(scheduled),
            },
            "squad_coverage": {
                "clubs": squad_teams,
                "players": squad_players,
                "last_updated": latest_squad_update,
            },
        }
