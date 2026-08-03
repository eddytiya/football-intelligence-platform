from datetime import datetime
from typing import List

from app.models.match import Match
from app.repositories.match_repository import MatchRepository
from datetime import datetime
from typing import List

class TeamAnalytics:
    """
    Provides football analytics for a team.

    This service is responsible for calculating team statistics
    from historical match data.

    This class DOES NOT:
    - Query the database directly
    - Train ML models
    - Use Pandas
    - Save CSV files
    """

    def __init__(self, repository: MatchRepository):
        """
        Initialize the analytics service.

        Parameters
        ----------
        repository : MatchRepository
            Repository used to retrieve match data.
        """
        self.repository = repository

    def get_previous_matches(
        self,
        team_id: int,
        before_date: datetime | None,
        limit: int = 5,
    ) -> List[Match]:
        """
        Return the team's previous finished matches before the specified date.
        """

        # If the current match has no utc_date, there is no reliable
        # reference point for historical lookups.
        if before_date is None:
            return []

        return self.repository.get_previous_matches(
            team_id=team_id,
            before_date=before_date,
            limit=limit,
        )
    

    def get_head_to_head_matches(
        self,
        home_team_id: int,
        away_team_id: int,
        before_date: datetime | None,
        limit: int = 5,
    ) -> List[Match]:
        """
        Return previous meetings between two teams.
        """

        if before_date is None:
            return []

        return self.repository.get_head_to_head_matches(
            home_team_id=home_team_id,
            away_team_id=away_team_id,
            before_date=before_date,
            limit=limit,
        )
    def build_league_table(
        self,
        before_date: datetime | None,
    ) -> dict:
        """
        Build the league table using all finished matches
        before the specified date.

        Returns
        -------
        dict
            {
                team_id: {
                    ...
                }
            }
        """

        # If the current match has no utc_date,
        # a league table cannot be built.
        if before_date is None:
            return {}

        matches = self.repository.get_finished_matches_before(
            before_date=before_date,
        )

        table = {}

        for match in matches:

            home = match.home_team_id
            away = match.away_team_id

            if home not in table:
                table[home] = {
                    "matches": 0,
                    "wins": 0,
                    "draws": 0,
                    "losses": 0,
                    "points": 0,
                    "goals_scored": 0,
                    "goals_conceded": 0,
                }

            if away not in table:
                table[away] = {
                    "matches": 0,
                    "wins": 0,
                    "draws": 0,
                    "losses": 0,
                    "points": 0,
                    "goals_scored": 0,
                    "goals_conceded": 0,
                }

            table[home]["matches"] += 1
            table[away]["matches"] += 1

            table[home]["goals_scored"] += match.home_score
            table[home]["goals_conceded"] += match.away_score

            table[away]["goals_scored"] += match.away_score
            table[away]["goals_conceded"] += match.home_score

            if match.home_score > match.away_score:

                table[home]["wins"] += 1
                table[home]["points"] += 3

                table[away]["losses"] += 1

            elif match.home_score < match.away_score:

                table[away]["wins"] += 1
                table[away]["points"] += 3

                table[home]["losses"] += 1

            else:

                table[home]["draws"] += 1
                table[away]["draws"] += 1

                table[home]["points"] += 1
                table[away]["points"] += 1

        ranking = sorted(
            table.items(),
            key=lambda item: (
                item[1]["points"],
                item[1]["goals_scored"] - item[1]["goals_conceded"],
                item[1]["goals_scored"],
            ),
            reverse=True,
        )

        for position, (team_id, stats) in enumerate(ranking, start=1):

            stats["league_position"] = position

            stats["goal_difference"] = (
                stats["goals_scored"] -
                stats["goals_conceded"]
            )

            stats["points_per_game"] = (
                round(
                    stats["points"] / stats["matches"],
                    2,
                )
                if stats["matches"] > 0
                else 0.0
            )

        return table
    
    def calculate_league_statistics(
        self,
        team_id: int,
        before_date: datetime | None,
    ) -> dict:
        """
        Calculate league table statistics for a team
        before the specified date.
        """

        # If the current match has no utc_date,
        # league statistics cannot be calculated.
        if before_date is None:
            return {
                "league_position": 0,
                "league_matches": 0,
                "league_wins": 0,
                "league_draws": 0,
                "league_losses": 0,
                "league_points": 0,
                "league_goals_scored": 0,
                "league_goals_conceded": 0,
                "league_goal_difference": 0,
                "league_points_per_game": 0.0,
            }

        table = self.build_league_table(
            before_date=before_date,
        )

        if team_id not in table:

            return {
                "league_position": 0,
                "league_matches": 0,
                "league_wins": 0,
                "league_draws": 0,
                "league_losses": 0,
                "league_points": 0,
                "league_goals_scored": 0,
                "league_goals_conceded": 0,
                "league_goal_difference": 0,
                "league_points_per_game": 0.0,
            }

        stats = table[team_id]

        return {
            "league_position": stats["league_position"],
            "league_matches": stats["matches"],
            "league_wins": stats["wins"],
            "league_draws": stats["draws"],
            "league_losses": stats["losses"],
            "league_points": stats["points"],
            "league_goals_scored": stats["goals_scored"],
            "league_goals_conceded": stats["goals_conceded"],
            "league_goal_difference": stats["goal_difference"],
            "league_points_per_game": stats["points_per_game"],
        }

    def calculate_opponent_strength_statistics(
        self,
        team_id: int,
        before_date: datetime | None,
        last_n: int = 5,
    ) -> dict:
        """
        Calculate statistics describing the quality of the
        opponents faced in the previous matches.

        Returns
        -------
        dict
            Opponent strength features.
        """

        # If there is no reference date, return default values.
        if before_date is None:
            return {
                "average_opponent_position": 0.0,
                "average_opponent_points": 0.0,
                "average_opponent_goal_difference": 0.0,
                "average_opponent_points_per_game": 0.0,
                "average_opponent_win_rate": 0.0,
                "average_opponent_goals_scored": 0.0,
                "average_opponent_goals_conceded": 0.0,
                "strong_opponents_faced": 0,
                "top4_opponents_faced": 0,
                "top6_opponents_faced": 0,
                "bottom6_opponents_faced": 0,
            }

        matches = self.get_previous_matches(
            team_id=team_id,
            before_date=before_date,
            limit=last_n,
        )

        league_table = self.build_league_table(
            before_date=before_date,
        )

        opponent_positions = []
        opponent_points = []
        opponent_goal_difference = []
        opponent_points_per_game = []
        opponent_win_rates = []
        opponent_goals_scored = []
        opponent_goals_conceded = []

        strong_opponents = 0
        top4 = 0
        top6 = 0
        bottom6 = 0

        for match in matches:

            opponent_id = (
                match.away_team_id
                if match.home_team_id == team_id
                else match.home_team_id
            )

            opponent = league_table.get(opponent_id)

            if opponent is None:
                continue

            matches_played = opponent["matches"]

            win_rate = (
                (opponent["wins"] / matches_played) * 100
                if matches_played > 0
                else 0.0
            )

            opponent_positions.append(opponent["league_position"])
            opponent_points.append(opponent["points"])
            opponent_goal_difference.append(opponent["goal_difference"])
            opponent_points_per_game.append(opponent["points_per_game"])
            opponent_win_rates.append(round(win_rate, 2))
            opponent_goals_scored.append(opponent["goals_scored"])
            opponent_goals_conceded.append(opponent["goals_conceded"])

            position = opponent["league_position"]

            if position <= 4:
                top4 += 1

            if position <= 6:
                top6 += 1

            if position >= 15:
                bottom6 += 1

            if position <= 8:
                strong_opponents += 1

        if not opponent_positions:

            return {
                "average_opponent_position": 0.0,
                "average_opponent_points": 0.0,
                "average_opponent_goal_difference": 0.0,
                "average_opponent_points_per_game": 0.0,
                "average_opponent_win_rate": 0.0,
                "average_opponent_goals_scored": 0.0,
                "average_opponent_goals_conceded": 0.0,
                "strong_opponents_faced": 0,
                "top4_opponents_faced": 0,
                "top6_opponents_faced": 0,
                "bottom6_opponents_faced": 0,
            }

        return {
            "average_opponent_position": round(
                sum(opponent_positions) / len(opponent_positions),
                2,
            ),
            "average_opponent_points": round(
                sum(opponent_points) / len(opponent_points),
                2,
            ),
            "average_opponent_goal_difference": round(
                sum(opponent_goal_difference) / len(opponent_goal_difference),
                2,
            ),
            "average_opponent_points_per_game": round(
                sum(opponent_points_per_game) / len(opponent_points_per_game),
                2,
            ),
            "average_opponent_win_rate": round(
                sum(opponent_win_rates) / len(opponent_win_rates),
                2,
            ),
            "average_opponent_goals_scored": round(
                sum(opponent_goals_scored) / len(opponent_goals_scored),
                2,
            ),
            "average_opponent_goals_conceded": round(
                sum(opponent_goals_conceded) / len(opponent_goals_conceded),
                2,
            ),
            "strong_opponents_faced": strong_opponents,
            "top4_opponents_faced": top4,
            "top6_opponents_faced": top6,
            "bottom6_opponents_faced": bottom6,
        }


    def filter_matches_by_venue(
        self,
        matches: List[Match],
        team_id: int,
        venue: str,
    ) -> List[Match]:
        """
        Filter matches by venue.

        Parameters
        ----------
        venue : str
            "home" or "away"
        """

        if venue == "home":
            return [
                match
                for match in matches
                if match.home_team_id == team_id
            ]

        if venue == "away":
            return [
                match
                for match in matches
                if match.away_team_id == team_id
            ]

        return matches

    def calculate_result_statistics(
        self,
        matches: List[Match],
        team_id: int,
    ) -> dict:
        """
        Calculate result statistics from a list of matches.

        This method performs no database queries.

        Parameters
        ----------
        matches : list[Match]
            Previously fetched matches.

        team_id : int
            Team ID.
        """

        wins = 0
        draws = 0
        losses = 0
        points = 0

        for match in matches:

            is_home = match.home_team_id == team_id

            team_score = match.home_score if is_home else match.away_score
            opponent_score = match.away_score if is_home else match.home_score

            if team_score > opponent_score:
                wins += 1
                points += 3

            elif team_score == opponent_score:
                draws += 1
                points += 1

            else:
                losses += 1

        return {
            "matches": len(matches),
            "wins": wins,
            "draws": draws,
            "losses": losses,
            "points": points,
        }

    def get_result_statistics(
        self,
        team_id: int,
        before_date: datetime,
        last_n: int = 5,
    ) -> dict:
        """
        Fetch previous matches and calculate
        result statistics.
        """

        matches = self.get_previous_matches(
            team_id=team_id,
            before_date=before_date,
            limit=last_n,
        )

        return self.calculate_result_statistics(
            matches=matches,
            team_id=team_id,
        )

    def calculate_goal_statistics(
        self,
        matches: List[Match],
        team_id: int,
    ) -> dict:
        """
        Calculate goal statistics from a list of matches.

        This method performs no database queries.

        Parameters
        ----------
        matches : list[Match]
            Previously fetched matches.

        team_id : int
            Team ID.
        """

        goals_scored = 0
        goals_conceded = 0

        for match in matches:

            is_home = match.home_team_id == team_id

            goals_scored += match.home_score if is_home else match.away_score
            goals_conceded += match.away_score if is_home else match.home_score

        total_matches = len(matches)

        if total_matches == 0:
            average_scored = 0.0
            average_conceded = 0.0
        else:
            average_scored = goals_scored / total_matches
            average_conceded = goals_conceded / total_matches

        return {
            "goals_scored": goals_scored,
            "goals_conceded": goals_conceded,
            "goal_difference": goals_scored - goals_conceded,
            "average_goals_scored": round(average_scored, 2),
            "average_goals_conceded": round(average_conceded, 2),
        }
    
    def calculate_form_statistics(
        self,
        matches: List[Match],
        team_id: int,
    ) -> dict:
        """
        Calculate recent form statistics.

        Form Example:
            WWDLW

        Returns
        -------
        dict
        """

        form = []

        wins = 0
        draws = 0
        losses = 0

        # Matches are returned newest -> oldest.
        # Reverse them so the form reads oldest -> newest.
        ordered_matches = list(reversed(matches))

        for match in ordered_matches:

            is_home = match.home_team_id == team_id

            team_score = match.home_score if is_home else match.away_score
            opponent_score = match.away_score if is_home else match.home_score

            if team_score > opponent_score:
                form.append("W")
                wins += 1

            elif team_score == opponent_score:
                form.append("D")
                draws += 1

            else:
                form.append("L")
                losses += 1

        matches_played = len(matches)

        form_points = (wins * 3) + draws

        max_points = matches_played * 3

        form_percentage = (
            round((form_points / max_points) * 100, 2)
            if max_points > 0
            else 0.0
        )

        win_rate = (
            round((wins / matches_played) * 100, 2)
            if matches_played > 0
            else 0.0
        )

        return {
            "form": "".join(form),
            "form_points": form_points,
            "form_percentage": form_percentage,
            "win_rate": win_rate,
        }
    
    def calculate_venue_statistics(
        self,
        matches: List[Match],
        team_id: int,
    ) -> dict:
        """
        Calculate venue specific statistics.

        If the team is the home team, only previous
        home matches are considered.

        If the team is the away team, only previous
        away matches are considered.
        """

        home_matches = self.filter_matches_by_venue(
            matches,
            team_id,
            "home",
        )

        away_matches = self.filter_matches_by_venue(
            matches,
            team_id,
            "away",
        )

        home_result = self.calculate_result_statistics(
            home_matches,
            team_id,
        )

        away_result = self.calculate_result_statistics(
            away_matches,
            team_id,
        )

        home_goal = self.calculate_goal_statistics(
            home_matches,
            team_id,
        )

        away_goal = self.calculate_goal_statistics(
            away_matches,
            team_id,
        )

        home_form = self.calculate_form_statistics(
            home_matches,
            team_id,
        )

        away_form = self.calculate_form_statistics(
            away_matches,
            team_id,
        )

        return {

            # Home Venue

            "home_matches_only": home_result["matches"],
            "home_wins_only": home_result["wins"],
            "home_draws_only": home_result["draws"],
            "home_losses_only": home_result["losses"],
            "home_points_only": home_result["points"],

            "home_goals_scored_only":
                home_goal["goals_scored"],

            "home_goals_conceded_only":
                home_goal["goals_conceded"],

            "home_goal_difference_only":
                home_goal["goal_difference"],

            "home_avg_goals_scored_only":
                home_goal["average_goals_scored"],

            "home_avg_goals_conceded_only":
                home_goal["average_goals_conceded"],

            "home_form_only":
                home_form["form"],

            "home_form_points_only":
                home_form["form_points"],

            "home_form_percentage_only":
                home_form["form_percentage"],

            "home_win_rate_only":
                home_form["win_rate"],

            # Away Venue

            "away_matches_only": away_result["matches"],
            "away_wins_only": away_result["wins"],
            "away_draws_only": away_result["draws"],
            "away_losses_only": away_result["losses"],
            "away_points_only": away_result["points"],

            "away_goals_scored_only":
                away_goal["goals_scored"],

            "away_goals_conceded_only":
                away_goal["goals_conceded"],

            "away_goal_difference_only":
                away_goal["goal_difference"],

            "away_avg_goals_scored_only":
                away_goal["average_goals_scored"],

            "away_avg_goals_conceded_only":
                away_goal["average_goals_conceded"],

            "away_form_only":
                away_form["form"],

            "away_form_points_only":
                away_form["form_points"],

            "away_form_percentage_only":
                away_form["form_percentage"],

            "away_win_rate_only":
                away_form["win_rate"],
        }
    
    def calculate_streak_statistics(
        self,
        matches: List[Match],
        team_id: int,
    ) -> dict:
        """
        Calculate different streak statistics.

        The matches are assumed to be ordered
        newest -> oldest.
        """

        win_streak = 0
        draw_streak = 0
        loss_streak = 0
        unbeaten_streak = 0
        clean_sheet_streak = 0
        failed_to_score_streak = 0

        # ---------- Win Streak ----------
        for match in matches:

            is_home = match.home_team_id == team_id

            team_score = match.home_score if is_home else match.away_score
            opponent_score = match.away_score if is_home else match.home_score

            if team_score > opponent_score:
                win_streak += 1
            else:
                break

        # ---------- Draw Streak ----------
        for match in matches:

            is_home = match.home_team_id == team_id

            team_score = match.home_score if is_home else match.away_score
            opponent_score = match.away_score if is_home else match.home_score

            if team_score == opponent_score:
                draw_streak += 1
            else:
                break

        # ---------- Loss Streak ----------
        for match in matches:

            is_home = match.home_team_id == team_id

            team_score = match.home_score if is_home else match.away_score
            opponent_score = match.away_score if is_home else match.home_score

            if team_score < opponent_score:
                loss_streak += 1
            else:
                break

        # ---------- Unbeaten ----------
        for match in matches:

            is_home = match.home_team_id == team_id

            team_score = match.home_score if is_home else match.away_score
            opponent_score = match.away_score if is_home else match.home_score

            if team_score >= opponent_score:
                unbeaten_streak += 1
            else:
                break

        # ---------- Clean Sheets ----------
        for match in matches:

            is_home = match.home_team_id == team_id

            opponent_score = match.away_score if is_home else match.home_score

            if opponent_score == 0:
                clean_sheet_streak += 1
            else:
                break

        # ---------- Failed To Score ----------
        for match in matches:

            is_home = match.home_team_id == team_id

            team_score = match.home_score if is_home else match.away_score

            if team_score == 0:
                failed_to_score_streak += 1
            else:
                break

        return {
            "win_streak": win_streak,
            "draw_streak": draw_streak,
            "loss_streak": loss_streak,
            "unbeaten_streak": unbeaten_streak,
            "clean_sheet_streak": clean_sheet_streak,
            "failed_to_score_streak": failed_to_score_streak,
        }
    
    def calculate_momentum_statistics(
        self,
        matches: List[Match],
        team_id: int,
    ) -> dict:
        """
        Calculate momentum statistics using the
        last 3 and last 5 matches.
        """

        last_3 = matches[:3]
        last_5 = matches[:5]

        def calculate_points(match_list):

            points = 0

            for match in match_list:

                is_home = match.home_team_id == team_id

                team_score = match.home_score if is_home else match.away_score
                opponent_score = match.away_score if is_home else match.home_score

                if team_score > opponent_score:
                    points += 3

                elif team_score == opponent_score:
                    points += 1

            return points

        def calculate_goals_scored(match_list):

            goals = 0

            for match in match_list:

                if match.home_team_id == team_id:
                    goals += match.home_score
                else:
                    goals += match.away_score

            return goals

        def calculate_goals_conceded(match_list):

            goals = 0

            for match in match_list:

                if match.home_team_id == team_id:
                    goals += match.away_score
                else:
                    goals += match.home_score

            return goals

        points_last_3 = calculate_points(last_3)
        points_last_5 = calculate_points(last_5)

        goals_scored_last_3 = calculate_goals_scored(last_3)
        goals_scored_last_5 = calculate_goals_scored(last_5)

        goals_conceded_last_3 = calculate_goals_conceded(last_3)
        goals_conceded_last_5 = calculate_goals_conceded(last_5)

        average_points_last_3 = (
            round(points_last_3 / len(last_3), 2)
            if last_3
            else 0.0
        )

        average_points_last_5 = (
            round(points_last_5 / len(last_5), 2)
            if last_5
            else 0.0
        )

        return {

            "points_last_3": points_last_3,
            "points_last_5": points_last_5,

            "average_points_last_3": average_points_last_3,
            "average_points_last_5": average_points_last_5,

            "goals_scored_last_3": goals_scored_last_3,
            "goals_scored_last_5": goals_scored_last_5,

            "goals_conceded_last_3": goals_conceded_last_3,
            "goals_conceded_last_5": goals_conceded_last_5,
        }
    def calculate_head_to_head_statistics(
        self,
        home_team_id: int,
        away_team_id: int,
        before_date: datetime,
        last_n: int = 5,
    ) -> dict:
        """
        Calculate head-to-head statistics.
        """

        matches = self.get_head_to_head_matches(
            home_team_id=home_team_id,
            away_team_id=away_team_id,
            before_date=before_date,
            limit=last_n,
        )

        home_wins = 0
        away_wins = 0
        draws = 0

        home_goals = 0
        away_goals = 0

        form = []

        for match in reversed(matches):

            home_goals += match.home_score
            away_goals += match.away_score

            if match.home_score > match.away_score:

                if match.home_team_id == home_team_id:
                    home_wins += 1
                    form.append("W")
                else:
                    away_wins += 1
                    form.append("L")

            elif match.home_score < match.away_score:

                if match.away_team_id == home_team_id:
                    home_wins += 1
                    form.append("W")
                else:
                    away_wins += 1
                    form.append("L")

            else:
                draws += 1
                form.append("D")

        total = len(matches)

        home_rate = (
            round((home_wins / total) * 100, 2)
            if total > 0
            else 0.0
        )

        away_rate = (
            round((away_wins / total) * 100, 2)
            if total > 0
            else 0.0
        )

        home_form_points = (home_wins * 3) + draws
        away_form_points = (away_wins * 3) + draws

        return {
            "h2h_matches": total,

            "h2h_home_wins": home_wins,
            "h2h_away_wins": away_wins,
            "h2h_draws": draws,

            "h2h_home_goals": home_goals,
            "h2h_away_goals": away_goals,

            "h2h_goal_difference": home_goals - away_goals,

            "h2h_home_win_rate": home_rate,
            "h2h_away_win_rate": away_rate,

            "h2h_home_form_points": home_form_points,
            "h2h_away_form_points": away_form_points,

            "h2h_form": "".join(form),
        }
    def get_goal_statistics(
        self,
        team_id: int,
        before_date: datetime,
        last_n: int = 5,
    ) -> dict:
        """
        Fetch previous matches and calculate
        goal statistics.
        """

        matches = self.get_previous_matches(
            team_id=team_id,
            before_date=before_date,
            limit=last_n,
        )

        return self.calculate_goal_statistics(
            matches=matches,
            team_id=team_id,
        )

    def build_team_features(
        self,
        team_id: int,
        before_date: datetime,
        last_n: int = 5,
    ) -> dict:
        """
        Build a complete feature set for a team before a match.

        This method performs a single repository call and reuses
        the retrieved matches for all calculations.
        """

        matches = self.get_previous_matches(
            team_id=team_id,
            before_date=before_date,
            limit=last_n,
        )

        result_stats = self.calculate_result_statistics(
            matches=matches,
            team_id=team_id,
        )

        goal_stats = self.calculate_goal_statistics(
            matches=matches,
            team_id=team_id,
        )

        form_stats = self.calculate_form_statistics(
            matches=matches,
            team_id=team_id,
        )

        venue_stats = self.calculate_venue_statistics(
            matches=matches,
            team_id=team_id,
        )

        streak_stats = self.calculate_streak_statistics(
            matches=matches,
            team_id=team_id,
        )

        momentum_stats = self.calculate_momentum_statistics(
            matches=matches,
            team_id=team_id,
        )

        league_stats = self.calculate_league_statistics(
            team_id=team_id,
            before_date=before_date,
        )

        opponent_strength_stats = self.calculate_opponent_strength_statistics(
            team_id=team_id,
            before_date=before_date,
            last_n=last_n,
        )

        return {
            **result_stats,
            **goal_stats,
            **form_stats,
            **venue_stats,
            **streak_stats,
            **momentum_stats,
            **league_stats,
            **opponent_strength_stats,
        }