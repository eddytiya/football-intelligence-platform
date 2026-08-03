from app.db.session import SessionLocal
from app.services.machine_learning.prediction_service import PredictionService


def main():
    db = SessionLocal()

    service = PredictionService(db)

    print("\n" + "=" * 70)
    print("Prediction By ID")
    print("=" * 70)

    prediction = service.get_prediction(1)

    print(prediction)

    print("\n" + "=" * 70)
    print("Prediction By Match")
    print("=" * 70)

    prediction = service.get_match_prediction(1)

    print(prediction)

    print("\n" + "=" * 70)
    print("Today's Predictions")
    print("=" * 70)

    predictions = service.get_todays_predictions()

    print(f"Found {len(predictions)} prediction(s).")

    db.close()


if __name__ == "__main__":
    main()