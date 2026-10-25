from datetime import datetime, timezone

import pytest

from app.services.etl import prediction_history_sync as sync

NOW = datetime(2026, 10, 17, tzinfo=timezone.utc)


def csv(date="12/10/2026", home=2, away=0, outcome="H"):
    return f"Date,HomeTeam,AwayTeam,FTHG,FTAG,FTR\n{date},A,B,{home},{away},{outcome}\n".encode()


@pytest.mark.parametrize("content,error", [
    (csv("18/10/2026"), "future"),
    (csv("12/10/2025"), "season"),
    (csv(home=-1), "scoreline"),
    (csv(outcome="A"), "disagrees"),
    (b"<html>not a CSV</html>", "columns"),
])
def test_rejects_invalid_provider_history(content, error):
    with pytest.raises(ValueError, match=error):
        sync.validate_download(content, 2026, NOW)


def test_accepts_valid_history_and_ignores_unplayed_rows():
    content = csv() + b"20/10/2026,C,D,,,\n"
    frame, latest = sync.validate_download(content, 2026, NOW)
    assert len(frame) == 1
    assert latest == "2026-10-12"


def test_failed_refresh_preserves_existing_file(tmp_path, monkeypatch):
    monkeypatch.setattr(sync, "DATA_DIR", tmp_path / "data")
    monkeypatch.setattr(sync, "REPORTS_DIR", tmp_path / "reports")
    monkeypatch.setattr(sync.HistoricalDownloader, "LEAGUES", {"PL": "E0"})
    path = tmp_path / "data" / "raw" / "historical" / "PL_2026.csv"
    path.parent.mkdir(parents=True)
    path.write_bytes(csv())

    class Response:
        content = csv("18/10/2026")

        def raise_for_status(self):
            return None

    monkeypatch.setattr(sync.httpx, "get", lambda *a, **k: Response())
    report = sync.refresh_history(NOW)
    assert report[0]["status"] == "unavailable"
    assert path.read_bytes() == csv()
