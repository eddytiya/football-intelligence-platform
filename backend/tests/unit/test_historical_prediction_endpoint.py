from datetime import datetime, timedelta
from types import SimpleNamespace

import pytest
from fastapi import HTTPException

from app.api import prediction as api


def fixture(status="SCHEDULED", kickoff=None):
    return SimpleNamespace(id=1, status=status, utc_date=kickoff or datetime.utcnow() + timedelta(days=1),
                           competition=SimpleNamespace(code="PL"), home_team=SimpleNamespace(name="A"),
                           away_team=SimpleNamespace(name="B"))


@pytest.mark.parametrize("record", [fixture("QUARANTINED"), fixture("FINISHED"), fixture(kickoff=datetime(2000, 1, 1))])
def test_non_prematch_fixture_rejected_before_model_call(monkeypatch, record):
    monkeypatch.setattr(api, "MatchRepository", lambda db: SimpleNamespace(get_match_by_id=lambda key: record))
    monkeypatch.setattr(api, "get_historical_model", lambda: pytest.fail("Model must not run"))
    with pytest.raises(HTTPException) as error:
        api.get_historical_prediction(1, object())
    assert error.value.status_code == 422


def test_unresolved_model_history_returns_readable_422(monkeypatch):
    monkeypatch.setattr(api, "MatchRepository", lambda db: SimpleNamespace(get_match_by_id=lambda key: fixture()))

    def reject(**kwargs):
        raise ValueError("Verified team history is unavailable")

    monkeypatch.setattr(api, "get_historical_model", lambda: SimpleNamespace(predict_fixture=reject))
    with pytest.raises(HTTPException) as error:
        api.get_historical_prediction(1, object())
    assert error.value.status_code == 422
    assert "Verified team history" in error.value.detail
