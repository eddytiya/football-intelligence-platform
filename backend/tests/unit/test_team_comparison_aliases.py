from datetime import datetime, timedelta
from types import SimpleNamespace

from app.api.team import compare_teams
from app.models.team import Team


def test_comparison_attributes_home_alias_win_to_selected_club():
    first = SimpleNamespace(id=1, name="Manchester United FC", crest=None)
    second = SimpleNamespace(id=2, name="Arsenal FC", crest=None)
    alias = SimpleNamespace(id=3, name="Man United", crest=None)
    fixture = SimpleNamespace(
        id=100, home_team_id=3, away_team_id=2, home_team=alias, away_team=second,
        home_score=3, away_score=1, utc_date=datetime.utcnow() - timedelta(days=10),
        status="FINISHED", competition=None, competition_id=None, match_week=None,
    )
    selected = iter([first, second])

    class Query:
        def __init__(self, model): self.model = model
        def filter(self, *args): return self
        def options(self, *args): return self
        def first(self): return next(selected)
        def all(self): return [first, second, alias] if self.model is Team else [fixture]

    result = compare_teams(1, 2, SimpleNamespace(query=lambda model: Query(model)))
    assert result["first_team_wins"] == 1
    assert result["second_team_wins"] == 0
    assert result["first_team_goals"] == 3
    assert result["second_team_goals"] == 1
    assert result["recent_meetings"][0]["home_team_id"] == 3
