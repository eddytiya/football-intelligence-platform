"""Verify repaired artifact and database quarantine without changing either."""
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import joblib
import numpy as np
import pandas as pd
from sqlalchemy import text
from app.core.paths import REPORTS_DIR
from app.db.database import engine
from app.services.machine_learning.historical_match_model import HistoricalMatchModel


def main():
    output = REPORTS_DIR / "data_repairs"
    path = output / "repaired_model.joblib"
    artifact = joblib.load(path)
    model = HistoricalMatchModel.load(path)
    assert model.feature_schema_version == 2
    matches = model.load_matches()
    membership = {(league, int(season)): len(set(rows.home_team) | set(rows.away_team))
                  for (league, season), rows in matches.groupby(["league", "season"])}
    invalid_positions = [r for r in artifact["historical_examples"]
                         if any(r["features"][key] > membership[(r["league"], r["season"])]
                                for key in ("home_league_position", "away_league_position"))]
    assert not invalid_positions
    assert np.isfinite(pd.DataFrame([r["features"] for r in artifact["historical_examples"]]).to_numpy()).all()
    mappings = pd.read_csv(REPORTS_DIR / "data_audit" / "database_team_mappings.csv")
    resolved, unresolved = [], []
    for row in mappings.itertuples():
        if row.league not in model.known_teams:
            continue
        canonical, confidence = model._resolve_team(row.league, row.provider_name)
        record = {"league": row.league, "provider_name": row.provider_name, "canonical": canonical}
        (resolved if confidence == 1 else unresolved).append(record)
    pd.DataFrame(resolved).to_csv(output / "verified_mappings.csv", index=False)
    pd.DataFrame(unresolved).to_csv(output / "unresolved_mappings.csv", index=False)
    assert model._resolve_team("PL", "Leeds United FC") == ("leeds", 1.)
    assert model._resolve_team("PL", "Coventry City FC")[0] == "coventry"
    assert model._resolve_team("PD", "RCD Espanyol de Barcelona") == ("espanol", 1.)
    assert model._resolve_team("PPL", "Sport Lisboa e Benfica") == ("benfica", 1.)
    engine.echo = False
    with engine.connect() as connection:
        connection.execute(text("SET TRANSACTION READ ONLY"))
        counts = connection.execute(text("SELECT status, count(*) FROM matches GROUP BY status")).all()
        future_finished = connection.execute(text("SELECT count(*) FROM matches WHERE status='FINISHED' AND utc_date > :now"),
                                             {"now": datetime.now(timezone.utc).replace(tzinfo=None)}).scalar()
        fixtures = pd.read_sql(text("SELECT m.id, c.code AS league, h.name AS home_team, a.name AS away_team, m.utc_date FROM matches m JOIN competitions c ON c.id=m.competition_id JOIN teams h ON h.id=m.home_team_id JOIN teams a ON a.id=m.away_team_id WHERE m.status IN ('SCHEDULED','TIMED') AND m.utc_date > :now ORDER BY m.utc_date LIMIT 250"), connection, params={"now": datetime.now(timezone.utc).replace(tzinfo=None)})
    assert future_finished == 0
    smoke = []
    for row in fixtures.itertuples():
        if row.league not in model.known_teams:
            continue
        try:
            prediction = model.predict_fixture(row.league, row.home_team, row.away_team, row.utc_date)
        except ValueError:
            continue
        p = [prediction[key] for key in ("away_win_probability", "draw_probability", "home_win_probability")]
        assert abs(sum(p) - 1) <= .0002
        assert prediction["prediction_status"] == "ready"
        smoke.append({"match_id": row.id, "league": row.league, "home_team": row.home_team,
                      "away_team": row.away_team, "history_through": prediction["history_through"]})
        if len(smoke) >= 4:
            break
    assert smoke, "No supported upcoming fixture could be forecast"
    report = {"snapshots": len(artifact["historical_examples"]), "invalid_positions": len(invalid_positions),
              "verified_mappings": len(resolved), "unresolved_mapping_count": len(unresolved),
              "unresolved_mappings": unresolved,
              "database_status_counts": dict(counts), "future_finished_remaining": future_finished,
              "smoke_forecasts": smoke,
              "website_validation": artifact["metrics"]["website_ensemble"]}
    (output / "verification.json").write_text(json.dumps(report, indent=2, default=str), encoding="utf-8")
    print(json.dumps(report, indent=2, default=str))


if __name__ == "__main__":
    main()
