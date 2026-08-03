from sqlalchemy.orm import Session

from app.repositories.competition_repository import (
    CompetitionRepository,
)
from app.schemas.competition import (
    CompetitionResponse,
)


class CompetitionService:
    """
    Service responsible for football
    competition business logic.
    """

    def __init__(self, db: Session):
        self.repository = CompetitionRepository(db)

    def get_all_competitions(
        self,
    ) -> list[CompetitionResponse]:
        """
        Return all competitions.
        """

        competitions = (
            self.repository.get_all_competitions()
        )

        return [
            CompetitionResponse(
                id=competition.id,
                name=competition.name,
                code=competition.code,
                emblem=competition.emblem,
                type=competition.type,
                area_name=competition.area_name,
                area_flag=competition.area_flag,
                seasons_available=competition.seasons_available,
                match_count=len(competition.matches),
                scheduled_match_count=sum(match.status == "SCHEDULED" for match in competition.matches),
            )
            for competition in competitions
        ]
