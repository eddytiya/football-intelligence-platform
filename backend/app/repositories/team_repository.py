from sqlalchemy.orm import Session

from app.models.team import Team


class TeamRepository:
    """
    Repository responsible for retrieving
    team data from the database.

    This class ONLY interacts with the database.
    """

    def __init__(self, db: Session):
        """
        Initialize the repository.

        Parameters
        ----------
        db : Session
            SQLAlchemy database session.
        """
        self.db = db

    # ==========================================================
    # Get By ID
    # ==========================================================

    def get_team_by_id(
        self,
        team_id: int,
    ) -> Team | None:
        """
        Return a team by its database ID.
        """

        return (
            self.db.query(Team)
            .filter(Team.id == team_id)
            .first()
        )

    # ==========================================================
    # Get By API ID
    # ==========================================================

    def get_team_by_api_id(
        self,
        api_id: int,
    ) -> Team | None:
        """
        Return a team by its Football-Data API ID.
        """

        return (
            self.db.query(Team)
            .filter(Team.api_id == api_id)
            .first()
        )

    # ==========================================================
    # Get By Name
    # ==========================================================

    def get_team_by_name(
        self,
        name: str,
    ) -> Team | None:
        """
        Return a team by its name.
        """

        return (
            self.db.query(Team)
            .filter(Team.name == name)
            .first()
        )

    # ==========================================================
    # Get All
    # ==========================================================

    def get_all_teams(self) -> list[Team]:
        """
        Return all teams ordered by name.
        """

        return (
            self.db.query(Team)
            .order_by(Team.name.asc())
            .all()
        )

    # ==========================================================
    # Exists
    # ==========================================================

    def team_exists(
        self,
        team_id: int,
    ) -> bool:
        """
        Check whether a team exists.
        """

        return (
            self.db.query(Team)
            .filter(Team.id == team_id)
            .first()
            is not None
        )

    def api_team_exists(
        self,
        api_id: int,
    ) -> bool:
        """
        Check whether a Football-Data API team exists.
        """

        return (
            self.db.query(Team)
            .filter(Team.api_id == api_id)
            .first()
            is not None
        )