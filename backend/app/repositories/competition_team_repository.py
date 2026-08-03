from sqlalchemy.orm import Session

from app.models.competition_team import CompetitionTeam


class CompetitionTeamRepository:
    """
    Repository responsible for Competition-Team database operations.
    """

    def __init__(self, db: Session):
        self.db = db

    # ==========================================================
    # Get By ID
    # ==========================================================

    def get_by_id(
        self,
        competition_team_id: int,
    ) -> CompetitionTeam | None:

        return (
            self.db.query(CompetitionTeam)
            .filter(
                CompetitionTeam.id == competition_team_id
            )
            .first()
        )

    # ==========================================================
    # Get By Competition & Team
    # ==========================================================

    def get_by_competition_and_team(
        self,
        competition_id: int,
        team_id: int,
    ) -> CompetitionTeam | None:

        return (
            self.db.query(CompetitionTeam)
            .filter(
                CompetitionTeam.competition_id == competition_id,
                CompetitionTeam.team_id == team_id,
            )
            .first()
        )

    # ==========================================================
    # Get Competition Teams
    # ==========================================================

    def get_competition_teams(
        self,
        competition_id: int,
    ) -> list[CompetitionTeam]:

        return (
            self.db.query(CompetitionTeam)
            .filter(
                CompetitionTeam.competition_id == competition_id
            )
            .all()
        )

    # ==========================================================
    # Get Team Competitions
    # ==========================================================

    def get_team_competitions(
        self,
        team_id: int,
    ) -> list[CompetitionTeam]:

        return (
            self.db.query(CompetitionTeam)
            .filter(
                CompetitionTeam.team_id == team_id
            )
            .all()
        )

    # ==========================================================
    # Get All
    # ==========================================================

    def get_all(self) -> list[CompetitionTeam]:

        return (
            self.db.query(CompetitionTeam)
            .order_by(
                CompetitionTeam.competition_id,
                CompetitionTeam.team_id,
            )
            .all()
        )

    # ==========================================================
    # Exists
    # ==========================================================

    def exists(
        self,
        competition_id: int,
        team_id: int,
    ) -> bool:

        return (
            self.db.query(CompetitionTeam)
            .filter(
                CompetitionTeam.competition_id == competition_id,
                CompetitionTeam.team_id == team_id,
            )
            .first()
            is not None
        )

    # ==========================================================
    # Create
    # ==========================================================

    def create(
        self,
        competition_team: CompetitionTeam,
    ) -> CompetitionTeam:

        self.db.add(competition_team)
        self.db.commit()
        self.db.refresh(competition_team)

        return competition_team

    # ==========================================================
    # Delete
    # ==========================================================

    def delete(
        self,
        competition_team: CompetitionTeam,
    ):

        self.db.delete(competition_team)
        self.db.commit()