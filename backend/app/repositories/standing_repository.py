from sqlalchemy.orm import Session

from app.models.standing import Standing


class StandingRepository:
    """
    Repository responsible for Standing database operations.
    """

    def __init__(self, db: Session):
        self.db = db

    # ==========================================================
    # Get By ID
    # ==========================================================

    def get_by_id(
        self,
        standing_id: int,
    ) -> Standing | None:

        return (
            self.db.query(Standing)
            .filter(
                Standing.id == standing_id
            )
            .first()
        )

    # ==========================================================
    # Get By Competition
    # ==========================================================

    def get_by_competition(
        self,
        competition_id: int,
    ) -> list[Standing]:

        return (
            self.db.query(Standing)
            .filter(
                Standing.competition_id == competition_id
            )
            .order_by(
                Standing.position
            )
            .all()
        )

    # ==========================================================
    # Get By Season
    # ==========================================================

    def get_by_season(
        self,
        season_id: int,
    ) -> list[Standing]:

        return (
            self.db.query(Standing)
            .filter(
                Standing.season_id == season_id
            )
            .order_by(
                Standing.position
            )
            .all()
        )

    # ==========================================================
    # Get By Team
    # ==========================================================

    def get_by_team(
        self,
        team_id: int,
    ) -> list[Standing]:

        return (
            self.db.query(Standing)
            .filter(
                Standing.team_id == team_id
            )
            .all()
        )

    # ==========================================================
    # Get By Competition + Season + Team
    # ==========================================================

    def get_by_competition_season_team(
        self,
        competition_id: int,
        season_id: int,
        team_id: int,
    ) -> Standing | None:

        return (
            self.db.query(Standing)
            .filter(
                Standing.competition_id == competition_id,
                Standing.season_id == season_id,
                Standing.team_id == team_id,
            )
            .first()
        )

    # ==========================================================
    # Get All
    # ==========================================================

    def get_all(self) -> list[Standing]:

        return (
            self.db.query(Standing)
            .order_by(
                Standing.competition_id,
                Standing.season_id,
                Standing.position,
            )
            .all()
        )

    # ==========================================================
    # Exists
    # ==========================================================

    def exists(
        self,
        competition_id: int,
        season_id: int,
        team_id: int,
    ) -> bool:

        return (
            self.db.query(Standing)
            .filter(
                Standing.competition_id == competition_id,
                Standing.season_id == season_id,
                Standing.team_id == team_id,
            )
            .first()
            is not None
        )

    # ==========================================================
    # Create
    # ==========================================================

    def create(
        self,
        standing: Standing,
    ) -> Standing:

        self.db.add(standing)
        self.db.commit()
        self.db.refresh(standing)

        return standing

    # ==========================================================
    # Delete
    # ==========================================================

    def delete(
        self,
        standing: Standing,
    ):

        self.db.delete(standing)
        self.db.commit()