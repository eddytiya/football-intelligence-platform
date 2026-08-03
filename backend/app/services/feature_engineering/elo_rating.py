
from math import log, pow
from statistics import mean, pstdev

class EloRatingService:
    """
    Maintains Elo ratings for all teams.

    Ratings are updated chronologically so that every
    match only uses information available before kickoff.
    """

    BASE_RATING = 1500.0
    K_FACTOR = 20
    HOME_ADVANTAGE = 100

    K_FACTORS = {

        # Domestic leagues
        "PL": 20,
        "BL1": 20,
        "SA": 20,
        "PD": 20,
        "FL1": 20,
        "DED": 20,
        "PPL": 20,
        "BSA": 20,

        # Domestic cups
        "FAC": 25,
        "ELC": 25,
        "DFB": 25,
        "CDR": 25,
        "CUP": 25,

        # European competitions
        "CL": 30,
        "EL": 28,
        "ECL": 26,

        # International tournaments
        "WC": 40,
        "EC": 35,
        "COPA": 35,
    }

    def __init__(self):
        """
        Maintain three separate Elo rating systems.

        overall_ratings:
            General team strength.

        home_ratings:
            Team strength when playing at home.

        away_ratings:
            Team strength when playing away.
        """

        self.overall_ratings = {}

        self.home_ratings = {}

        self.away_ratings = {}

        # Rating history
        self.overall_history = {}

        self.home_history = {}

        self.away_history = {}
            

    

    

    def get_overall_elo(
        self,
        team_id: int,
    ) -> float:
        """
        Return the team's overall Elo.
        """

        return self.overall_ratings.get(
            team_id,
            self.BASE_RATING,
        )


    def get_home_elo(
        self,
        team_id: int,
    ) -> float:
        """
        Return the team's home Elo.
        """

        return self.home_ratings.get(
            team_id,
            self.BASE_RATING,
        )


    def get_away_elo(
        self,
        team_id: int,
    ) -> float:
        """
        Return the team's away Elo.
        """

        return self.away_ratings.get(
            team_id,
            self.BASE_RATING,
        )

    def _append_history(
        self,
        history: dict,
        team_id: int,
        rating: float,
    ) -> None:
        """
        Store a team's rating history.
        """

        history.setdefault(
            team_id,
            [],
        ).append(
            round(
                rating,
                2,
            )
        )


    def _get_history(
        self,
        history: dict,
        team_id: int,
    ) -> list[float]:
        """
        Return a team's rating history.
        """

        return history.get(
            team_id,
            [],
        )

    def get_last_5_average(
        self,
        history: dict,
        team_id: int,
    ) -> float:
        """
        Return the average Elo from the team's last
        five recorded ratings.
        """

        ratings = self._get_history(
            history,
            team_id,
        )

        if not ratings:
            return self.BASE_RATING

        last_five = ratings[-5:]

        return round(
            mean(last_five),
            2,
        )
    def get_momentum(
        self,
        history: dict,
        team_id: int,
        current_rating: float,
    ) -> float:
        """
        Return the difference between the current Elo
        and the team's average Elo over the last five matches.
        """

        average_rating = self.get_last_5_average(
            history,
            team_id,
        )

        return round(
            current_rating - average_rating,
            2,
        )


    def get_trend(
        self,
        history: dict,
        team_id: int,
        current_rating: float,
    ) -> float:
        """
        Return the Elo change between the current rating
        and the oldest rating in the team's last five matches.
        """

        ratings = self._get_history(
            history,
            team_id,
        )

        if not ratings:
            return 0.0

        last_five = ratings[-5:]

        oldest_rating = last_five[0]

        return round(
            current_rating - oldest_rating,
            2,
        )

    def get_volatility(
        self,
        history: dict,
        team_id: int,
    ) -> float:
        """
        Return the standard deviation of the team's
        last five Elo ratings.
        """

        ratings = self._get_history(
            history,
            team_id,
        )

        if len(ratings) < 2:
            return 0.0

        last_five = ratings[-5:]

        return round(
            pstdev(last_five),
            2,
        )


    def get_peak_rating(
        self,
        history: dict,
        team_id: int,
    ) -> float:
        """
        Return the highest Elo rating from the team's
        last five matches.
        """

        ratings = self._get_history(
            history,
            team_id,
        )

        if not ratings:
            return self.BASE_RATING

        return round(
            max(ratings[-5:]),
            2,
        )


    def get_low_rating(
        self,
        history: dict,
        team_id: int,
    ) -> float:
        """
        Return the lowest Elo rating from the team's
        last five matches.
        """

        ratings = self._get_history(
            history,
            team_id,
        )

        if not ratings:
            return self.BASE_RATING

        return round(
            min(ratings[-5:]),
            2,
        )
    def get_win_streak(
        self,
        history: dict,
        team_id: int,
    ) -> int:
        """
        Return the number of consecutive Elo increases
        in the team's last five ratings.
        """

        ratings = self._get_history(
            history,
            team_id,
        )

        if len(ratings) < 2:
            return 0

        last_five = ratings[-5:]

        streak = 0

        for i in range(
            len(last_five) - 1,
            0,
            -1,
        ):
            if last_five[i] > last_five[i - 1]:
                streak += 1
            else:
                break

        return streak


    def get_loss_streak(
        self,
        history: dict,
        team_id: int,
    ) -> int:
        """
        Return the number of consecutive Elo decreases
        in the team's last five ratings.
        """

        ratings = self._get_history(
            history,
            team_id,
        )

        if len(ratings) < 2:
            return 0

        last_five = ratings[-5:]

        streak = 0

        for i in range(
            len(last_five) - 1,
            0,
            -1,
        ):
            if last_five[i] < last_five[i - 1]:
                streak += 1
            else:
                break

        return streak


    def get_gap_to_peak(
        self,
        history: dict,
        team_id: int,
        current_rating: float,
    ) -> float:
        """
        Return the distance between the current Elo
        and the highest Elo from the last five ratings.
        """

        peak_rating = self.get_peak_rating(
            history,
            team_id,
        )

        return round(
            current_rating - peak_rating,
            2,
        )
    def expected_score(
        self,
        team_rating: float,
        opponent_rating: float,
        home_advantage: float = 0.0,
    ) -> float:
        """
        Calculate the expected result.
        """

        return 1 / (
            1
            + pow(
                10,
                (
                    opponent_rating
                    - (team_rating + home_advantage)
                )
                / 400,
            )
        )

    def goal_margin_multiplier(
        self,
        home_rating: float,
        away_rating: float,
        home_score: int,
        away_score: int,
    ) -> float:
        """
        Calculate the goal margin multiplier.

        Bigger wins produce larger Elo changes while
        accounting for the rating difference between teams.
        """

        goal_difference = abs(home_score - away_score)

        # Draws or one-goal games receive the normal update.
        if goal_difference <= 1:
            return 1.0

        rating_difference = abs(home_rating - away_rating)

        multiplier = (
            log(goal_difference + 1)
            * (
                2.2
                / (
                    0.001 * rating_difference
                    + 2.2
                )
            )
        )

        return multiplier
    

    def get_k_factor(
        self,
        competition_code: str | None,
    ) -> int:
        """
        Return the K-factor based on the competition.

        Higher importance competitions receive larger
        Elo adjustments.
        """

        if competition_code is None:
            return self.K_FACTOR

        return self.K_FACTORS.get(
            competition_code.upper(),
            self.K_FACTOR,
        )

    def update_elo(
        self,
        home_team_id: int,
        away_team_id: int,
        home_score: int,
        away_score: int,
        competition_code: str | None = None,
    ) -> None:
        """
        Update Overall, Home and Away Elo ratings after a match.
        """

        # -----------------------------
        # Overall Elo
        # -----------------------------
        overall_home = self.get_overall_elo(home_team_id)
        overall_away = self.get_overall_elo(away_team_id)

        expected_home = self.expected_score(
            overall_home,
            overall_away,
            self.HOME_ADVANTAGE,
        )

        expected_away = self.expected_score(
            overall_away,
            overall_home,
        )

        # -----------------------------
        # Match Result
        # -----------------------------
        if home_score > away_score:
            actual_home = 1.0
            actual_away = 0.0

        elif home_score < away_score:
            actual_home = 0.0
            actual_away = 1.0

        else:
            actual_home = 0.5
            actual_away = 0.5

        k_factor = self.get_k_factor(
            competition_code,
        )

        margin_multiplier = self.goal_margin_multiplier(
            overall_home,
            overall_away,
            home_score,
            away_score,
        )

        # -----------------------------
        # Update Overall Elo
        # -----------------------------
        overall_home_new = (
            overall_home
            + (
                k_factor
                * margin_multiplier
                * (actual_home - expected_home)
            )
        )

        overall_away_new = (
            overall_away
            + (
                k_factor
                * margin_multiplier
                * (actual_away - expected_away)
            )
        )

        self.overall_ratings[home_team_id] = round(
            overall_home_new,
            2,
        )

        self._append_history(
            self.overall_history,
            home_team_id,
            overall_home_new,
        )

        self.overall_ratings[away_team_id] = round(
            overall_away_new,
            2,
        )

        self._append_history(
            self.overall_history,
            away_team_id,
            overall_away_new,
        )

        # -----------------------------
        # Home / Away Elo
        # -----------------------------
        home_home_rating = self.get_home_elo(home_team_id)

        away_away_rating = self.get_away_elo(away_team_id)

        expected_home = self.expected_score(
            home_home_rating,
            away_away_rating,
            self.HOME_ADVANTAGE,
        )

        expected_away = self.expected_score(
            away_away_rating,
            home_home_rating,
        )

        home_home_new = (
            home_home_rating
            + (
                k_factor
                * margin_multiplier
                * (actual_home - expected_home)
            )
        )

        away_away_new = (
            away_away_rating
            + (
                k_factor
                * margin_multiplier
                * (actual_away - expected_away)
            )
        )

        self.home_ratings[home_team_id] = round(
            home_home_new,
            2,
        )

        self._append_history(
            self.home_history,
            home_team_id,
            home_home_new,
        )

        self.away_ratings[away_team_id] = round(
            away_away_new,
            2,
        )

        self._append_history(
            self.away_history,
            away_team_id,
            away_away_new,
        )

    def get_match_features(
        self,
        home_team_id: int,
        away_team_id: int,
    ) -> dict:
        """
        Return all Elo ratings BEFORE the match.
        """

        # -----------------------------
        # Overall Elo
        # -----------------------------
        overall_home = self.get_overall_elo(
            home_team_id,
        )

        overall_away = self.get_overall_elo(
            away_team_id,
        )

        # -----------------------------
        # Home / Away Elo
        # -----------------------------
        home_home = self.get_home_elo(
            home_team_id,
        )

        away_away = self.get_away_elo(
            away_team_id,
        )

        # -----------------------------
        # Average Elo (Last 5 Matches)
        # -----------------------------
        home_elo_last_5_avg = self.get_last_5_average(
            self.overall_history,
            home_team_id,
        )

        away_elo_last_5_avg = self.get_last_5_average(
            self.overall_history,
            away_team_id,
        )

        # -----------------------------
        # Elo Momentum
        # -----------------------------
        home_elo_momentum = self.get_momentum(
            self.overall_history,
            home_team_id,
            overall_home,
        )

        away_elo_momentum = self.get_momentum(
            self.overall_history,
            away_team_id,
            overall_away,
        )

        # -----------------------------
        # Elo Trend
        # -----------------------------
        home_elo_trend = self.get_trend(
            self.overall_history,
            home_team_id,
            overall_home,
        )

        away_elo_trend = self.get_trend(
            self.overall_history,
            away_team_id,
            overall_away,
        )
        # -----------------------------
        # Elo Volatility
        # -----------------------------
        home_elo_volatility = self.get_volatility(
            self.overall_history,
            home_team_id,
        )

        away_elo_volatility = self.get_volatility(
            self.overall_history,
            away_team_id,
        )

        # -----------------------------
        # Elo Peak
        # -----------------------------
        home_elo_peak = self.get_peak_rating(
            self.overall_history,
            home_team_id,
        )

        away_elo_peak = self.get_peak_rating(
            self.overall_history,
            away_team_id,
        )

        # -----------------------------
        # Elo Low
        # -----------------------------
        home_elo_low = self.get_low_rating(
            self.overall_history,
            home_team_id,
        )

        away_elo_low = self.get_low_rating(
            self.overall_history,
            away_team_id,
        )

        # -----------------------------
        # Elo Streaks
        # -----------------------------
        home_elo_win_streak = self.get_win_streak(
            self.overall_history,
            home_team_id,
        )

        away_elo_win_streak = self.get_win_streak(
            self.overall_history,
            away_team_id,
        )

        home_elo_loss_streak = self.get_loss_streak(
            self.overall_history,
            home_team_id,
        )

        away_elo_loss_streak = self.get_loss_streak(
            self.overall_history,
            away_team_id,
        )

        # -----------------------------
        # Gap To Peak
        # -----------------------------
        home_elo_gap_to_peak = self.get_gap_to_peak(
            self.overall_history,
            home_team_id,
            overall_home,
        )

        away_elo_gap_to_peak = self.get_gap_to_peak(
            self.overall_history,
            away_team_id,
            overall_away,
        )
                # -----------------------------
        # Win Probabilities (Overall Elo)
        # -----------------------------
        home_win_probability = self.expected_score(
            overall_home,
            overall_away,
            self.HOME_ADVANTAGE,
        )

        away_win_probability = self.expected_score(
            overall_away,
            overall_home,
        )

        # -----------------------------
        # Win Probabilities (Home/Away Elo)
        # -----------------------------
        home_home_win_probability = self.expected_score(
            home_home,
            away_away,
            self.HOME_ADVANTAGE,
        )

        away_away_win_probability = self.expected_score(
            away_away,
            home_home,
        )

        return {

            # -----------------------------
            # Overall Elo
            # -----------------------------
            "home_elo": round(
                overall_home,
                2,
            ),

            "away_elo": round(
                overall_away,
                2,
            ),

            "elo_difference": round(
                overall_home - overall_away,
                2,
            ),

            "home_elo_last_5_avg": home_elo_last_5_avg,

            "away_elo_last_5_avg": away_elo_last_5_avg,
            "home_elo_momentum": home_elo_momentum,

            "away_elo_momentum": away_elo_momentum,

            "home_elo_trend": home_elo_trend,

            "away_elo_trend": away_elo_trend,
            "home_elo_volatility": home_elo_volatility,
            "away_elo_volatility": away_elo_volatility,

            "home_elo_peak": home_elo_peak,
            "away_elo_peak": away_elo_peak,

            "home_elo_low": home_elo_low,
            "away_elo_low": away_elo_low,

            "home_elo_win_streak": home_elo_win_streak,
            "away_elo_win_streak": away_elo_win_streak,

            "home_elo_loss_streak": home_elo_loss_streak,
            "away_elo_loss_streak": away_elo_loss_streak,

            "home_elo_gap_to_peak": home_elo_gap_to_peak,
            "away_elo_gap_to_peak": away_elo_gap_to_peak,

            # -----------------------------
            # Home / Away Elo
            # -----------------------------
            "home_home_elo": round(
                home_home,
                2,
            ),

            "away_away_elo": round(
                away_away,
                2,
            ),

            "home_away_elo_difference": round(
                home_home - away_away,
                2,
            ),

            # -----------------------------
            # Win Probabilities
            # -----------------------------
            "home_win_probability": round(
                home_win_probability,
                4,
            ),

            "away_win_probability": round(
                away_win_probability,
                4,
            ),

            "home_home_win_probability": round(
                home_home_win_probability,
                4,
            ),

            "away_away_win_probability": round(
                away_away_win_probability,
                4,
            ),
        }