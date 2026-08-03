from datetime import date, datetime, timedelta

from sqlalchemy.orm import Session, joinedload

from app.models.match import Match
from app.models.prediction import Prediction


class PredictionRepository:
    """
    Repository responsible for all database operations
    related to machine learning predictions.

    This class ONLY interacts with the database.

    Responsibilities
    ----------------
    - Save predictions
    - Retrieve predictions
    - Retrieve today's predictions
    - Retrieve competition predictions
    - Delete old predictions

    This class DOES NOT:
    - Generate ML features
    - Make predictions
    - Train models
    """

    def __init__(self, db: Session):
        """
        Initialize the repository.

        Parameters
        ----------
        db : Session
            SQLAlchemy database session.
        """
        self.db = db

    # ==========================================================
    # Create
    # ==========================================================

    def create_prediction(
        self,
        prediction: Prediction,
    ) -> Prediction:
        """
        Save a prediction.
        """

        self.db.add(prediction)
        self.db.commit()
        self.db.refresh(prediction)

        return prediction

    def save_prediction(
        self,
        match_id: int,
        model_name: str,
        prediction: str,
        home_probability: float,
        draw_probability: float,
        away_probability: float,
    ) -> Prediction:
        """
        Create and save a prediction.
        """

        existing_prediction = (
            self.get_prediction_by_match_id(
                match_id
            )
        )

        if existing_prediction:

            return self.update_prediction(
                prediction_record=existing_prediction,
                prediction=prediction,
                home_probability=home_probability,
                draw_probability=draw_probability,
                away_probability=away_probability,
                model_name=model_name,
            )

        prediction_record = Prediction(
            match_id=match_id,
            model_name=model_name,
            prediction=prediction,
            home_probability=home_probability,
            draw_probability=draw_probability,
            away_probability=away_probability,
        )

        return self.create_prediction(
            prediction_record
        )

    def update_prediction(
        self,
        prediction_record: Prediction,
        prediction: str,
        home_probability: float,
        draw_probability: float,
        away_probability: float,
        model_name: str,
    ) -> Prediction:
        """
        Update an existing prediction.
        """

        prediction_record.prediction = prediction
        prediction_record.home_probability = (
            home_probability
        )
        prediction_record.draw_probability = (
            draw_probability
        )
        prediction_record.away_probability = (
            away_probability
        )
        prediction_record.model_name = model_name

        self.db.commit()

        self.db.refresh(prediction_record)

        return prediction_record

    # ==========================================================
    # Read
    # ==========================================================

    def get_prediction_by_id(
        self,
        prediction_id: int,
    ) -> Prediction | None:
        """
        Return prediction by ID with all related match data.
        """

        return (
            self.db.query(Prediction)
            .options(
                joinedload(Prediction.match)
                .joinedload(Match.home_team),
                joinedload(Prediction.match)
                .joinedload(Match.away_team),
                joinedload(Prediction.match)
                .joinedload(Match.competition),
            )
            .filter(
                Prediction.id == prediction_id
            )
            .first()
        )

    def get_prediction_by_match_id(
        self,
        match_id: int,
    ) -> Prediction | None:
        """
        Return prediction for a match.
        """

        return (
            self.db.query(Prediction)
            .options(
                joinedload(Prediction.match)
                .joinedload(Match.home_team),
                joinedload(Prediction.match)
                .joinedload(Match.away_team),
                joinedload(Prediction.match)
                .joinedload(Match.competition),
            )
            .filter(
                Prediction.match_id == match_id
            )
            .first()
        )

    def get_predictions_by_competition(
        self,
        competition_id: int,
    ) -> list[Prediction]:
        """
        Return predictions for a competition.
        """

        return (
            self.db.query(Prediction)
            .options(
                joinedload(Prediction.match)
                .joinedload(Match.home_team),
                joinedload(Prediction.match)
                .joinedload(Match.away_team),
                joinedload(Prediction.match)
                .joinedload(Match.competition),
            )
            .join(Match)
            .filter(
                Match.competition_id == competition_id
            )
            .order_by(
                Match.utc_date.asc()
            )
            .all()
        )

    def get_todays_predictions(
        self,
    ) -> list[Prediction]:
        """
        Return today's predictions.
        """

        today = date.today()

        start = datetime.combine(
            today,
            datetime.min.time(),
        )

        end = start + timedelta(days=1)

        return (
            self.db.query(Prediction)
            .options(
                joinedload(Prediction.match)
                .joinedload(Match.home_team),
                joinedload(Prediction.match)
                .joinedload(Match.away_team),
                joinedload(Prediction.match)
                .joinedload(Match.competition),
            )
            .join(Match)
            .filter(
                Match.utc_date >= start,
                Match.utc_date < end,
            )
            .order_by(
                Match.utc_date.asc(),
            )
            .all()
        )

    def get_recent_predictions(
        self,
        limit: int = 20,
    ) -> list[Prediction]:
        """
        Return the most recent predictions.
        """

        return (
            self.db.query(Prediction)
            .options(
                joinedload(Prediction.match)
                .joinedload(Match.home_team),
                joinedload(Prediction.match)
                .joinedload(Match.away_team),
                joinedload(Prediction.match)
                .joinedload(Match.competition),
            )
            .order_by(
                Prediction.predicted_at.desc()
            )
            .limit(limit)
            .all()
        )

    def get_all_predictions(
        self,
    ) -> list[Prediction]:
        """
        Return all predictions.
        """

        return (
            self.db.query(Prediction)
            .options(
                joinedload(Prediction.match)
                .joinedload(Match.home_team),
                joinedload(Prediction.match)
                .joinedload(Match.away_team),
                joinedload(Match.competition),
            )
            .order_by(
                Prediction.predicted_at.desc()
            )
            .all()
        )

    # ==========================================================
    # Delete
    # ==========================================================

    def delete_prediction(
        self,
        prediction: Prediction,
    ) -> None:
        """
        Delete a prediction.
        """

        self.db.delete(prediction)
        self.db.commit()

    def delete_old_predictions(
        self,
        before_date: datetime,
    ) -> int:
        """
        Delete predictions created before
        the given date.

        Returns
        -------
        int
            Number of deleted rows.
        """

        deleted = (
            self.db.query(Prediction)
            .filter(
                Prediction.predicted_at < before_date,
            )
            .delete()
        )

        self.db.commit()

        return deleted