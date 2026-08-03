from app.services.feature_engineering.team_analytics import TeamAnalytics


class FeatureGenerator:
    """
    Generates machine learning features for football matches.

    This service uses TeamAnalytics to build feature vectors
    for both the home and away teams before a match.

    Responsibilities
    ----------------
    - Generate features for a single match
    - Generate features for an entire dataset (later)

    This class DOES NOT:
    - Train ML models
    - Save CSV files
    - Query all matches from the database
    """

    def __init__(self, analytics: TeamAnalytics):
        """
        Initialize the feature generator.

        Parameters
        ----------
        analytics : TeamAnalytics
            Analytics service used to calculate team statistics.
        """
        self.analytics = analytics

    def _build_feature_dictionary(
        self,
        home_team_id: int,
        away_team_id: int,
        match_date,
        home_score=None,
        away_score=None,
        match_id=None,
    ):
        """
        Build the complete feature dictionary.

        Shared by:
        - Historical dataset generation
        - Future match prediction
        """

        home_features = self.analytics.build_team_features(
            team_id=home_team_id,
            before_date=match_date,
        )

        away_features = self.analytics.build_team_features(
            team_id=away_team_id,
            before_date=match_date,
        )

        h2h_features = self.analytics.calculate_head_to_head_statistics(
            home_team_id=home_team_id,
            away_team_id=away_team_id,
            before_date=match_date,
        )

        features = {}

        # ==========================================================
        # Match Information
        # ==========================================================

        features["match_id"] = match_id
        features["match_date"] = match_date

        features["home_team_id"] = home_team_id
        features["away_team_id"] = away_team_id

        # ==========================================================
        # Home Team Features
        # ==========================================================

        for key, value in home_features.items():
            features[f"home_{key}"] = value

        # ==========================================================
        # Away Team Features
        # ==========================================================

        for key, value in away_features.items():
            features[f"away_{key}"] = value

        # ==========================================================
        # Head-to-Head Features
        # ==========================================================

        for key, value in h2h_features.items():
            features[key] = value

        # ==========================================================
        # Target Columns
        # ==========================================================

        features["home_score"] = home_score
        features["away_score"] = away_score

        return features

    def generate_match_features(self, match) -> dict:
        """
        Generate features for a historical match.
        """

        return self._build_feature_dictionary(
            home_team_id=match.home_team_id,
            away_team_id=match.away_team_id,
            match_date=match.utc_date,
            home_score=match.home_score,
            away_score=match.away_score,
            match_id=match.id,
        )

    def generate_prediction_features(
        self,
        home_team_id: int,
        away_team_id: int,
        match_date,
    ) -> dict:
        """
        Generate features for a future match.
        """

        return self._build_feature_dictionary(
            home_team_id=home_team_id,
            away_team_id=away_team_id,
            match_date=match_date,
            home_score=None,
            away_score=None,
            match_id=None,
        )