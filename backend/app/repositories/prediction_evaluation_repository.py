from typing import List, Optional

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.prediction_evaluation import PredictionEvaluation


class PredictionEvaluationRepository:
    """
    Repository for managing prediction evaluations.
    """

    def __init__(self, db: Session):
        self.db = db

    # ==========================================================
    # Create
    # ==========================================================

    def create_evaluation(
        self,
        prediction_id: int,
        actual_result: str,
        correct: bool,
    ) -> PredictionEvaluation:
        """
        Save a new prediction evaluation.
        """

        evaluation = PredictionEvaluation(
            prediction_id=prediction_id,
            actual_result=actual_result,
            correct=correct,
        )

        self.db.add(evaluation)
        self.db.commit()
        self.db.refresh(evaluation)

        return evaluation

    # ==========================================================
    # Get By ID
    # ==========================================================

    def get_by_id(
        self,
        evaluation_id: int,
    ) -> Optional[PredictionEvaluation]:
        """
        Retrieve an evaluation by its ID.
        """

        return (
            self.db.query(PredictionEvaluation)
            .filter(PredictionEvaluation.id == evaluation_id)
            .first()
        )

    # ==========================================================
    # Get By Prediction
    # ==========================================================

    def get_by_prediction(
        self,
        prediction_id: int,
    ) -> Optional[PredictionEvaluation]:
        """
        Retrieve evaluation for a prediction.
        """

        return (
            self.db.query(PredictionEvaluation)
            .filter(
                PredictionEvaluation.prediction_id == prediction_id
            )
            .first()
        )

    # ==========================================================
    # Get All
    # ==========================================================

    def get_all(self) -> List[PredictionEvaluation]:
        """
        Return every evaluation.
        """

        return (
            self.db.query(PredictionEvaluation)
            .order_by(
                PredictionEvaluation.evaluated_at.desc()
            )
            .all()
        )

    # ==========================================================
    # Accuracy
    # ==========================================================

    def get_accuracy(self) -> float:
        """
        Calculate overall prediction accuracy.
        """

        total = (
            self.db.query(PredictionEvaluation)
            .count()
        )

        if total == 0:
            return 0.0

        correct = (
            self.db.query(PredictionEvaluation)
            .filter(
                PredictionEvaluation.correct.is_(True)
            )
            .count()
        )

        return round((correct / total) * 100, 2)

    # ==========================================================
    # Delete
    # ==========================================================

    def delete(
        self,
        evaluation_id: int,
    ) -> bool:
        """
        Delete an evaluation.
        """

        evaluation = self.get_by_id(evaluation_id)

        if evaluation is None:
            return False

        self.db.delete(evaluation)
        self.db.commit()

        return True

    # ==========================================================
    # Statistics
    # ==========================================================

    def get_total_predictions(self) -> int:
        """
        Total evaluated predictions.
        """

        return (
            self.db.query(PredictionEvaluation)
            .count()
        )

    def get_correct_predictions(self) -> int:
        """
        Number of correct predictions.
        """

        return (
            self.db.query(PredictionEvaluation)
            .filter(
                PredictionEvaluation.correct.is_(True)
            )
            .count()
        )

    def get_incorrect_predictions(self) -> int:
        """
        Number of incorrect predictions.
        """

        return (
            self.db.query(PredictionEvaluation)
            .filter(
                PredictionEvaluation.correct.is_(False)
            )
            .count()
        )

    # ==========================================================
    # Exists
    # ==========================================================

    def exists(
        self,
        prediction_id: int,
    ) -> bool:
        """
        Check whether a prediction has already
        been evaluated.
        """

        return (
            self.db.query(PredictionEvaluation)
            .filter(
                PredictionEvaluation.prediction_id == prediction_id
            )
            .first()
            is not None
        )