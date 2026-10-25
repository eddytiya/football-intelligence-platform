"""Performance uses verified immutable server forecasts, never legacy predictions."""
from collections import Counter
from types import SimpleNamespace
from app.models.match import Match
from app.models.forecast_snapshot import ForecastSnapshot
from app.services.prediction.admin_review import genuine_snapshot, actual_outcome


class PredictionAnalyticsRepository:
    def __init__(self, db):
        seen = set()
        self.rows = []
        for snapshot, match in db.query(ForecastSnapshot, Match).join(Match, Match.id == ForecastSnapshot.match_id).order_by(ForecastSnapshot.generated_at).all():
            if match.id not in seen and genuine_snapshot(snapshot, match):
                seen.add(match.id)
                self.rows.append((snapshot, actual_outcome(match)))

    def get_total_predictions(self):
        return len(self.rows)

    def get_correct_predictions(self):
        return sum(actual is not None and snapshot.payload['predicted_outcome'] == actual for snapshot, actual in self.rows)

    def get_incorrect_predictions(self):
        return sum(actual is not None and snapshot.payload['predicted_outcome'] != actual for snapshot, actual in self.rows)

    def get_accuracy(self):
        settled = sum(actual is not None for _, actual in self.rows)
        return round(100 * self.get_correct_predictions() / settled, 2) if settled else 0.0

    def get_prediction_distribution(self):
        return dict(Counter(snapshot.payload['predicted_outcome'] for snapshot, _ in self.rows))

    def get_average_probabilities(self):
        def average(key):
            return sum(snapshot.payload[key] for snapshot, _ in self.rows) / len(self.rows) if self.rows else 0
        return SimpleNamespace(home=average('home_win_probability'), draw=average('draw_probability'), away=average('away_win_probability'))

    def get_daily_statistics(self):
        counts = Counter(str(snapshot.generated_at.date()) for snapshot, _ in self.rows)
        return [{'date': day, 'predictions': count} for day, count in sorted(counts.items())]
