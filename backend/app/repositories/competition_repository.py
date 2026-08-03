from sqlalchemy.orm import Session

from app.models.competition import Competition


class CompetitionRepository:
    """
    Repository responsible for Competition database operations.
    """

    def __init__(self, db: Session):
        self.db = db

    def get_all_competitions(self) -> list[Competition]:
        return (
            self.db.query(Competition)
            .order_by(Competition.name)
            .all()
        )

    def get_by_id(self, competition_id: int) -> Competition | None:
        return (
            self.db.query(Competition)
            .filter(Competition.id == competition_id)
            .first()
        )

    def get_by_api_id(self, api_id: int) -> Competition | None:
        return (
            self.db.query(Competition)
            .filter(Competition.api_id == api_id)
            .first()
        )

    def get_by_code(self, code: str) -> Competition | None:
        return (
            self.db.query(Competition)
            .filter(Competition.code == code)
            .first()
        )

    def create(self, competition: Competition) -> Competition:
        self.db.add(competition)
        self.db.commit()
        self.db.refresh(competition)
        return competition

    def update(self, competition: Competition) -> Competition:
        self.db.commit()
        self.db.refresh(competition)
        return competition

    def delete(self, competition: Competition) -> None:
        self.db.delete(competition)
        self.db.commit()

    def get_or_create(self, api_id: int, defaults: dict):
        competition = self.get_by_api_id(api_id)

        if competition:
            return competition, False

        competition = Competition(
            api_id=api_id,
            **defaults,
        )

        self.db.add(competition)
        self.db.commit()
        self.db.refresh(competition)

        return competition, True