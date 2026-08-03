from app.repositories.dashboard_repository import DashboardRepository


class DashboardService:
    """
    Service responsible for dashboard operations.
    """

    def __init__(self, db):
        self.repository = DashboardRepository(db)

    def get_summary_statistics(self):
        """
        Get dashboard summary statistics.
        """
        return self.repository.get_summary_statistics()

    def get_recent_predictions(self):
        """
        Get recent predictions.
        """
        return self.repository.get_recent_predictions()

    def get_upcoming_matches(self):
        """
        Get upcoming matches.
        """
        return self.repository.get_upcoming_matches()

    def get_model_performance(self):
        """
        Get model performance.
        """
        return self.repository.get_model_performance()

    def get_dashboard(self):
        """
        Get complete dashboard data.
        """
        return {
            "summary": self.get_summary_statistics(),
            "recent_predictions": self.get_recent_predictions(),
            "upcoming_matches": self.get_upcoming_matches(),
            "model_performance": self.get_model_performance(),
        }

    def get_command_centre(self):
        return self.repository.get_command_centre()
