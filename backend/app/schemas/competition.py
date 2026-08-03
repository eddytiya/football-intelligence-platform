from pydantic import BaseModel, ConfigDict


class CompetitionResponse(BaseModel):
    """
    Response schema for a football competition.
    """

    model_config = ConfigDict(from_attributes=True)

    id: int

    name: str

    code: str

    emblem: str | None = None
    type: str | None = None
    area_name: str | None = None
    area_flag: str | None = None
    seasons_available: int | None = None
    match_count: int = 0
    scheduled_match_count: int = 0
