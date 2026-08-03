from app.repositories.prediction_analytics_repository import (
    PredictionAnalyticsRepository,
)


class PredictionAnalyticsService:
    """
    Service responsible for prediction analytics.
    """

    def __init__(self, db):
        self.repository = PredictionAnalyticsRepository(db)

    def get_overall_statistics(self):
        """
        Get overall prediction statistics.
        """
        return {
            "total_predictions": self.repository.get_total_predictions(),
            "correct_predictions": self.repository.get_correct_predictions(),
            "incorrect_predictions": self.repository.get_incorrect_predictions(),
            "accuracy": self.repository.get_accuracy(),
        }

    def get_prediction_distribution(self):
        """
        Get prediction distribution.
        """
        return self.repository.get_prediction_distribution()

    def get_average_probabilities(self):
        """
        Get average prediction probabilities.
        """
        averages = self.repository.get_average_probabilities()

        return {
            "home_probability": round(averages.home or 0, 2),
            "draw_probability": round(averages.draw or 0, 2),
            "away_probability": round(averages.away or 0, 2),
        }

    def get_daily_statistics(self):
        """
        Get daily prediction statistics.
        """
        return self.repository.get_daily_statistics()

    def get_dashboard_statistics(self):
        """
        Get complete analytics dashboard.
        """
        return {
            "overall": self.get_overall_statistics(),
            "distribution": self.get_prediction_distribution(),
            "average_probabilities": self.get_average_probabilities(),
            "daily_statistics": self.get_daily_statistics(),
        }