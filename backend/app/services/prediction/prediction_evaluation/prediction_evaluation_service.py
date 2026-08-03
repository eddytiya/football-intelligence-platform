from sqlalchemy.orm import Session

from app.repositories.match_repository import MatchRepository
from app.repositories.prediction_evaluation_repository import (
    PredictionEvaluationRepository,
)
from app.repositories.prediction_repository import PredictionRepository


class PredictionEvaluationService:
    """
    Handles business logic for evaluating
    machine learning predictions.
    """

    def __init__(self, db: Session):
        self.db = db

        self.match_repository = MatchRepository(db)

        self.prediction_repository = PredictionRepository(db)

        self.evaluation_repository = PredictionEvaluationRepository(db)

    # ==========================================================
    # Helper Methods
    # ==========================================================

    @staticmethod
    def determine_actual_result(match) -> str:
        """
        Determine the actual result of a finished match.
        """

        if match.home_score > match.away_score:
            return "Home Win"

        if match.home_score < match.away_score:
            return "Away Win"

        return "Draw"

    # ==========================================================
    # Evaluate Prediction
    # ==========================================================

    def evaluate_prediction(
        self,
        prediction_id: int,
    ):
        """
        Evaluate a prediction using
        the finished match result.
        """

        prediction = (
            self.prediction_repository.get_prediction_by_id(
                prediction_id
            )
        )

        if prediction is None:
            raise ValueError("Prediction not found.")

        if self.evaluation_repository.exists(
            prediction_id
        ):
            raise ValueError(
                "Prediction has already been evaluated."
            )

        match = (
            self.match_repository.get_match_by_id(
                prediction.match_id
            )
        )

        if match is None:
            raise ValueError("Match not found.")

        if match.status != "FINISHED":
            raise ValueError(
                "Match has not finished yet."
            )

        actual_result = self.determine_actual_result(
            match
        )

        correct = (
            prediction.prediction
            == actual_result
        )

        return (
            self.evaluation_repository.create_evaluation(
                prediction_id=prediction.id,
                actual_result=actual_result,
                correct=correct,
            )
        )

    # ==========================================================
    # Read
    # ==========================================================

    def get_evaluation(
        self,
        evaluation_id: int,
    ):
        return self.evaluation_repository.get_by_id(
            evaluation_id
        )

    def get_prediction_evaluation(
        self,
        prediction_id: int,
    ):
        return (
            self.evaluation_repository.get_by_prediction(
                prediction_id
            )
        )

    def get_all_evaluations(self):
        return self.evaluation_repository.get_all()

    # ==========================================================
    # Accuracy
    # ==========================================================

    def get_accuracy(self):
        return {
            "accuracy": self.evaluation_repository.get_accuracy(),
            "total_predictions": (
                self.evaluation_repository.get_total_predictions()
            ),
            "correct_predictions": (
                self.evaluation_repository.get_correct_predictions()
            ),
            "incorrect_predictions": (
                self.evaluation_repository.get_incorrect_predictions()
            ),
        }

    # ==========================================================
    # Delete
    # ==========================================================

    def delete_evaluation(
        self,
        evaluation_id: int,
    ):
        return self.evaluation_repository.delete(
            evaluation_id
        )