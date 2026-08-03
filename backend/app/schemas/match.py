from datetime import datetime

from pydantic import BaseModel, ConfigDict


class UpcomingMatchResponse(BaseModel):
    """
    Response schema for an upcoming football match.
    """

    model_config = ConfigDict(from_attributes=True)

    id: int

    competition_id: int
    competition_name: str | None = None
    competition_code: str | None = None
    competition_emblem: str | None = None

    home_team_id: int
    home_team_name: str | None = None
    home_team_crest: str | None = None

    away_team_id: int
    away_team_name: str | None = None
    away_team_crest: str | None = None

    utc_date: datetime | None

    status: str | None
    match_week: int | None = None


class MatchDetailResponse(BaseModel):
    """
    Response schema for detailed match information.
    """

    model_config = ConfigDict(from_attributes=True)

    id: int

    competition_id: int
    competition_name: str | None = None
    competition_code: str | None = None
    competition_emblem: str | None = None

    home_team_id: int
    home_team_name: str | None = None
    home_team_crest: str | None = None

    away_team_id: int
    away_team_name: str | None = None
    away_team_crest: str | None = None

    utc_date: datetime | None

    status: str | None

    home_score: int
    away_score: int
    match_week: int | None = None
