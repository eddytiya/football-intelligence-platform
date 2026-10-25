from functools import lru_cache
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.prediction import (
    PredictionBatchRequest,
    MatchPredictionResponse,
    PredictionDetail,
    PredictionResponse,
)
from app.services.prediction.prediction_service import PredictionService
from app.services.machine_learning.historical_match_model import HistoricalMatchModel
from app.repositories.match_repository import MatchRepository
from app.core.paths import MODELS_DIR, DATA_DIR

router = APIRouter(
    prefix="/predictions",
    tags=["Predictions"],
)


def get_historical_model() -> HistoricalMatchModel:
    """Invalidate saved states when either the artifact or accepted history changes."""
    artifact = MODELS_DIR / "historical_match_model.joblib"
    sources = tuple((path.name, path.stat().st_mtime_ns) for path in sorted((DATA_DIR / "raw" / "historical").glob("*.csv")))
    return _load_historical_model(artifact.stat().st_mtime_ns, sources)


@lru_cache(maxsize=2)
def _load_historical_model(artifact_stamp, sources):
    model = HistoricalMatchModel.load()
    from app.services.machine_learning.historical_match_model import FEATURE_SCHEMA_VERSION
    if model.feature_schema_version == FEATURE_SCHEMA_VERSION and any(stamp > artifact_stamp for _, stamp in sources):
        # Rebuild states from accepted provider results without retraining estimators.
        training_data_through = model.training_data_through
        model.build_training_data()
        model.training_data_through = training_data_through
    return model


@router.get("/model/status")
def get_prediction_model_status():
    import joblib
    path = MODELS_DIR / "historical_match_model.joblib"
    if not path.exists():
        raise HTTPException(status_code=503, detail="Prediction model is not available.")
    artifact = joblib.load(path)
    if artifact.get('leakage_protocol_version') != 1:
        raise HTTPException(status_code=503, detail='Model evaluation protocol is unverified. Retraining is required.')
    return {"feature_schema_version": artifact.get("feature_schema_version", 1),
            "trained_at": artifact.get("trained_at"), "validation": artifact.get("metrics", {}),
            "leakage_protocol_version": artifact.get('leakage_protocol_version'),
            "training_data_through": artifact.get('training_data_through'),
            "note": "Model selection and final chronological test periods are separate. Historical reviews use independently fitted earlier-cutoff models."}


@router.get("/historical/match/{match_id}")
def get_historical_prediction(
    match_id: int,
    db: Session = Depends(get_db),
):
    """Return the historical-model probabilities for one scheduled match."""
    match = MatchRepository(db).get_match_by_id(match_id)

    if match is None:
        raise HTTPException(status_code=404, detail="Match not found.")

    if match.competition is None or match.home_team is None or match.away_team is None:
        raise HTTPException(status_code=422, detail="Match is missing team or competition data.")
    kickoff = match.utc_date
    if kickoff is None or match.status not in {"SCHEDULED", "TIMED"}:
        raise HTTPException(status_code=422, detail="Pre-match forecasts are available only for verified upcoming fixtures.")
    if kickoff.replace(tzinfo=timezone.utc) <= datetime.now(timezone.utc):
        raise HTTPException(status_code=422, detail="This fixture has already reached kickoff.")

    try:
        prediction = get_historical_model().predict_fixture(
            league=match.competition.code,
            home_team=match.home_team.name,
            away_team=match.away_team.name,
            match_date=match.utc_date,
        )
        prediction["match_id"] = match.id
        from app.services.prediction.admin_review import save_snapshot
        save_snapshot(db, match, prediction, 'pre_match')
        return prediction
    except FileNotFoundError as exc:
        raise HTTPException(status_code=503, detail="Historical model has not been trained.") from exc
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

# ==========================================================
# Batch Predictions
# ==========================================================


@router.post(
    "/batch",
    response_model=list[MatchPredictionResponse],
)
def predict_matches(
    request: PredictionBatchRequest,
    db: Session = Depends(get_db),
):
    """
    Generate predictions for multiple matches.
    """

    prediction_service = PredictionService(db)

    return prediction_service.predict_matches(
        request.match_ids
    )

def predict_upcoming_matches(
        self,
        days: int = 7,
    ):
        """
        Generate predictions for all upcoming matches.
        """

        print()
        print("=" * 70)
        print("Predict Upcoming Matches")
        print("=" * 70)

        matches = self.repository.get_upcoming_matches()

        print(
            f"Upcoming Matches : {len(matches)}"
        )

        predictions = []

        for match in matches:

            result = self.predict_match(
                match.id
            )

            predictions.append(
                {
                    "match_id": match.id,
                    "prediction": result["prediction"],
                    "prediction_code": result["prediction_code"],
                    "home_probability": result["probabilities"]["Home Win"],
                    "draw_probability": result["probabilities"]["Draw"],
                    "away_probability": result["probabilities"]["Away Win"],
                }
            )

        return predictions
# ==========================================================
# Generate Prediction
# ==========================================================


@router.post(
    "/match/{match_id}",
    response_model=PredictionResponse,
)
def predict_match(
    match_id: int,
    db: Session = Depends(get_db),
):
    """
    Generate and save a prediction for a football match.
    """

    prediction_service = PredictionService(db)

    try:
        prediction = prediction_service.predict_match(match_id)

        return PredictionResponse(
            prediction=prediction["prediction"],
            prediction_code=prediction["prediction_code"],
            home_probability=prediction["probabilities"]["Home Win"],
            draw_probability=prediction["probabilities"]["Draw"],
            away_probability=prediction["probabilities"]["Away Win"],
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=404,
            detail=str(exc),
        )


# ==========================================================
# Upcoming Match Predictions
# ==========================================================


@router.get(
    "/upcoming",
)
def get_upcoming_predictions(
    db: Session = Depends(get_db),
):
    """
    Generate predictions for all upcoming matches.
    """

    prediction_service = PredictionService(db)

    return prediction_service.predict_upcoming_matches()


# ==========================================================
# Today's Predictions
# ==========================================================


@router.get(
    "/today",
    response_model=list[PredictionDetail],
)
def get_todays_predictions(
    db: Session = Depends(get_db),
):
    """
    Return today's predictions.
    """

    prediction_service = PredictionService(db)

    return prediction_service.get_todays_predictions()


# ==========================================================
# Prediction By Match
# ==========================================================


@router.get(
    "/match/{match_id}",
    response_model=PredictionDetail,
)
def get_match_prediction(
    match_id: int,
    db: Session = Depends(get_db),
):
    """
    Return prediction for a specific match.
    """

    prediction_service = PredictionService(db)

    prediction = prediction_service.get_match_prediction(
        match_id
    )

    if prediction is None:
        raise HTTPException(
            status_code=404,
            detail="Prediction not found.",
        )

    return prediction


# ==========================================================
# Predictions By Competition
# ==========================================================


@router.get(
    "/competition/{competition_id}",
    response_model=list[PredictionDetail],
)
def get_competition_predictions(
    competition_id: int,
    db: Session = Depends(get_db),
):
    """
    Return predictions for a competition.
    """

    prediction_service = PredictionService(db)

    return prediction_service.get_competition_predictions(
        competition_id
    )


# ==========================================================
# Prediction By Prediction ID
# ==========================================================


@router.get(
    "/{prediction_id}",
    response_model=PredictionDetail,
)
def get_prediction(
    prediction_id: int,
    db: Session = Depends(get_db),
):
    """
    Return prediction by prediction ID.
    """

    prediction_service = PredictionService(db)

    prediction = prediction_service.get_prediction(
        prediction_id
    )

    if prediction is None:
        raise HTTPException(
            status_code=404,
            detail="Prediction not found.",
        )

    return prediction


# ==========================================================
# Delete Prediction
# ==========================================================


@router.delete(
    "/{prediction_id}",
)
def delete_prediction(
    prediction_id: int,
    db: Session = Depends(get_db),
):
    """
    Delete a prediction.
    """

    prediction_service = PredictionService(db)

    deleted = prediction_service.delete_prediction(
        prediction_id
    )

    if not deleted:
        raise HTTPException(
            status_code=404,
            detail="Prediction not found.",
        )

    return {
        "message": "Prediction deleted successfully."
    }
