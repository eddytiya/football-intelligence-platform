from sqlalchemy.orm import Session

from app.models.season import Season


class SeasonRepository:
    """
    Repository responsible for retrieving
    season data from the database.

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

    def get_season_by_id(
        self,
        season_id: int,
    ) -> Season | None:
        """
        Return a season by its database ID.
        """

        return (
            self.db.query(Season)
            .filter(Season.id == season_id)
            .first()
        )

    # ==========================================================
    # Get By API ID
    # ==========================================================

    def get_season_by_api_id(
        self,
        api_id: int,
    ) -> Season | None:
        """
        Return a season by its API ID.
        """

        return (
            self.db.query(Season)
            .filter(Season.api_id == api_id)
            .first()
        )

    # ==========================================================
    # Get By Competition & Year
    # ==========================================================

    def get_season(
        self,
        competition_id: int,
        start_year: int,
    ) -> Season | None:
        """
        Return a season for a competition and start year.
        """

        return (
            self.db.query(Season)
            .filter(
                Season.competition_id == competition_id,
                Season.start_year == start_year,
            )
            .first()
        )

    # ==========================================================
    # Get All
    # ==========================================================

    def get_all_seasons(self) -> list[Season]:
        """
        Return all seasons ordered by start year.
        """

        return (
            self.db.query(Season)
            .order_by(
                Season.start_year.desc()
            )
            .all()
        )

    # ==========================================================
    # Exists
    # ==========================================================

    def season_exists(
        self,
        season_id: int,
    ) -> bool:
        """
        Check whether a season exists.
        """

        return (
            self.db.query(Season)
            .filter(Season.id == season_id)
            .first()
            is not None
        )

    def api_season_exists(
        self,
        api_id: int,
    ) -> bool:
        """
        Check whether an API season exists.
        """

        return (
            self.db.query(Season)
            .filter(Season.api_id == api_id)
            .first()
            is not None
        )