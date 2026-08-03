from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.prediction import Prediction
from app.models.prediction_evaluation import PredictionEvaluation


class PredictionAnalyticsRepository:
    """
    Repository responsible for prediction analytics.
    """

    def __init__(self, db: Session):
        self.db = db

    # ==========================================================
    # Overall Statistics
    # ==========================================================

    def get_total_predictions(self) -> int:
        return self.db.query(Prediction).count()

    def get_correct_predictions(self) -> int:
        return (
            self.db.query(PredictionEvaluation)
            .filter(PredictionEvaluation.correct.is_(True))
            .count()
        )

    def get_incorrect_predictions(self) -> int:
        return (
            self.db.query(PredictionEvaluation)
            .filter(PredictionEvaluation.correct.is_(False))
            .count()
        )

    def get_accuracy(self) -> float:
        total = self.get_total_predictions()

        if total == 0:
            return 0.0

        correct = self.get_correct_predictions()

        return round((correct / total) * 100, 2)

    # ==========================================================
    # Prediction Distribution
    # ==========================================================

    def get_prediction_distribution(self):
        results = (
            self.db.query(
                Prediction.prediction,
                func.count(Prediction.id).label("count"),
            )
            .group_by(Prediction.prediction)
            .all()
        )

        return {
            prediction: count
            for prediction, count in results
        }

    # ==========================================================
    # Average Probabilities
    # ==========================================================

    def get_average_probabilities(self):
        return (
            self.db.query(
                func.avg(Prediction.home_probability).label("home"),
                func.avg(Prediction.draw_probability).label("draw"),
                func.avg(Prediction.away_probability).label("away"),
            )
            .first()
        )

    # ==========================================================
    # Daily Statistics
    # ==========================================================

    def get_daily_statistics(self):
        return (
            self.db.query(
                func.date(Prediction.predicted_at).label("date"),
                func.count(Prediction.id).label("predictions"),
            )
            .group_by(func.date(Prediction.predicted_at))
            .order_by(func.date(Prediction.predicted_at))
            .all()
        )