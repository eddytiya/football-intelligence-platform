"""Read-only data, feature and historical error audit. No retraining or database writes."""
from __future__ import annotations

import json
import sys
from difflib import SequenceMatcher
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import joblib
import numpy as np
import pandas as pd
from sklearn.metrics import confusion_matrix, log_loss
from sqlalchemy import text

from app.core.paths import MODELS_DIR, REPORTS_DIR
from app.services.machine_learning.historical_match_model import HistoricalMatchModel, normalise_team_name

AS_OF = pd.Timestamp("2026-10-17")
KEY = ["league", "match_date", "home_team", "away_team"]
PROBS = ["away_probability", "draw_probability", "home_probability"]


def summarize(frame):
    p = frame[PROBS].to_numpy()
    actual = frame.actual.to_numpy(dtype=int)
    return {"matches": len(frame), "accuracy": float((p.argmax(axis=1) == actual).mean()),
            "log_loss": float(log_loss(actual, p, labels=[0, 1, 2]))}


def group_scores(frame, column):
    return [{column: str(key), **summarize(part)} for key, part in frame.groupby(column, observed=True)]


def main():
    out = REPORTS_DIR / "data_audit"
    out.mkdir(exist_ok=True)
    artifact = joblib.load(MODELS_DIR / "historical_match_model.joblib")
    historical = HistoricalMatchModel()
    file_checks, frames = [], []
    for path in sorted(historical.historical_dir.glob("*.csv")):
        raw = pd.read_csv(path, low_memory=False)
        league, season = path.stem.rsplit("_", 1)
        required = {"Date", "HomeTeam", "AwayTeam", "FTHG", "FTAG"}
        if not required.issubset(raw):
            file_checks.append({"file": path.name, "rows": len(raw), "missing_columns": sorted(required - set(raw))})
            continue
        dates = pd.to_datetime(raw.Date, format="%d/%m/%Y", errors="coerce")
        missing = dates.isna()
        dates.loc[missing] = pd.to_datetime(raw.loc[missing, "Date"], format="%d/%m/%y", errors="coerce")
        hg, ag = (pd.to_numeric(raw[col], errors="coerce") for col in ("FTHG", "FTAG"))
        valid = dates.notna() & hg.notna() & ag.notna() & raw.HomeTeam.notna() & raw.AwayTeam.notna()
        file_checks.append({"file": path.name, "rows": len(raw), "valid_rows": int(valid.sum()),
                            "invalid_dates": int(dates.isna().sum()), "missing_scores": int((hg.isna() | ag.isna()).sum()),
                            "missing_teams": int((raw.HomeTeam.isna() | raw.AwayTeam.isna()).sum()),
                            "discarded_rows": int((~valid).sum())})
        frame = pd.DataFrame({"league": league, "season": int(season), "match_date": dates,
                              "home_team": raw.HomeTeam, "away_team": raw.AwayTeam,
                              "home_goals": hg, "away_goals": ag, "source": path.name})[valid].copy()
        frame["actual"] = np.where(frame.home_goals > frame.away_goals, 2, np.where(frame.home_goals == frame.away_goals, 1, 0))
        frame["result_label_mismatch"] = False
        if "FTR" in raw:
            frame["result_label_mismatch"] = raw.loc[valid, "FTR"].notna() & (raw.loc[valid, "FTR"] != frame.actual.map({0: "A", 1: "D", 2: "H"}))
        frames.append(frame)
    matches = pd.concat(frames, ignore_index=True).sort_values(["match_date", "league", "season"], kind="stable").reset_index(drop=True)
    pd.DataFrame(file_checks).to_csv(out / "source_files.csv", index=False)
    duplicates = matches[matches.duplicated(KEY, keep=False)]
    duplicates.to_csv(out / "duplicate_fixtures.csv", index=False)
    examples = pd.DataFrame([{**e, "match_date": pd.Timestamp(e["match_date"])} for e in artifact["historical_examples"]])
    numeric = pd.DataFrame(examples.features.tolist())
    aligned = examples.merge(matches[KEY + ["season", "actual"]], on=KEY, how="left", validate="one_to_one")
    assert aligned.season.notna().all(), "Saved snapshot absent from source data"
    assert np.array_equal(aligned.actual.to_numpy(), examples.result.to_numpy()), "Snapshot/source labels differ"
    team_counts = matches.groupby(["league", "season"]).apply(
        lambda f: len(set(f.home_team) | set(f.away_team)), include_groups=False).to_dict()
    position_limit = np.array([team_counts[(r.league, r.season)] for r in aligned.itertuples()])
    position_bad = (numeric.home_league_position > position_limit) | (numeric.away_league_position > position_limit)
    feature_flags = pd.concat([aligned[KEY + ["season"]], numeric], axis=1)
    feature_flags[position_bad].to_csv(out / "positions_outside_season_team_count.csv", index=False)
    # Opening match snapshot for each league-season: counts should not be described as season counts.
    opening = feature_flags.sort_values("match_date").groupby(["league", "season"]).head(1)
    opening.to_csv(out / "season_opening_features.csv", index=False)
    feature_stats = numeric.describe().T
    feature_stats["missing"] = numeric.isna().sum()
    feature_stats["unique_values"] = numeric.nunique()
    feature_stats.to_csv(out / "feature_statistics.csv")
    # Prior-season top six defined from completed on-pitch results only, with no future season information.
    previous_top, promoted = {}, {}
    for (league, season), part in matches.groupby(["league", "season"]):
        table = {}
        for row in part.itertuples():
            for team, gf, ga in ((row.home_team, row.home_goals, row.away_goals), (row.away_team, row.away_goals, row.home_goals)):
                stats = table.setdefault(team, [0, 0, 0])
                stats[0] += 3 if gf > ga else 1 if gf == ga else 0
                stats[1] += gf - ga
                stats[2] += gf
        ranked = sorted(table, key=lambda team: tuple(-v for v in table[team]) + (team,))
        previous_top[(league, int(season) + 1)] = set(ranked[:6])
        next_teams = matches[(matches.league == league) & (matches.season == season + 1)]
        promoted[(league, int(season) + 1)] = (set(next_teams.home_team) | set(next_teams.away_team)) - set(table)
    prediction_path = REPORTS_DIR / "catboost_recency_experiment" / "baseline_test_predictions.csv"
    predictions = pd.read_csv(prediction_path, parse_dates=["date"])
    evaluation = aligned[aligned.match_date >= predictions.date.min()].reset_index(drop=True)
    assert len(evaluation) == len(predictions)
    assert np.array_equal(evaluation.match_date.to_numpy(), predictions.date.to_numpy())
    assert np.array_equal(evaluation.actual.to_numpy(), predictions.actual.to_numpy())
    for column in PROBS:
        evaluation[column] = predictions[column].to_numpy()
    evaluation["predicted"] = evaluation[PROBS].to_numpy().argmax(axis=1)
    evaluation["confidence"] = evaluation[PROBS].max(axis=1)
    evaluation["confidence_band"] = pd.cut(evaluation.confidence, [0, .4, .5, .6, .7, .8, 1], include_lowest=True)
    evaluation["outcome"] = evaluation.actual.map({0: "Away win", 1: "Draw", 2: "Home win"})
    evaluation["prior_top_six"] = [r.home_team in previous_top.get((r.league, r.season), set()) or r.away_team in previous_top.get((r.league, r.season), set()) for r in evaluation.itertuples()]
    evaluation["involves_promoted_team"] = [r.home_team in promoted.get((r.league, r.season), set()) or r.away_team in promoted.get((r.league, r.season), set()) for r in evaluation.itertuples()]
    evaluation.drop(columns=["features"]).to_csv(out / "evaluation_matches.csv", index=False)
    per_league, per_outcome = group_scores(evaluation, "league"), group_scores(evaluation, "outcome")
    pd.DataFrame(per_league).to_csv(out / "errors_by_league.csv", index=False)
    pd.DataFrame(group_scores(evaluation, "season")).to_csv(out / "errors_by_season.csv", index=False)
    pd.DataFrame(group_scores(evaluation, "confidence_band")).to_csv(out / "errors_by_confidence.csv", index=False)
    pl = evaluation[evaluation.league == "PL"]
    freshness = [{"league": league, "latest_result": str(part.match_date.max().date()),
                  "days_before_audit": (AS_OF - part.match_date.max()).days, "matches": len(part)}
                 for league, part in matches.groupby("league")]
    database = {"status": "not_checked"}
    try:
        from app.db.database import engine
        engine.echo = False
        with engine.connect() as connection:
            connection.execute(text("SET TRANSACTION READ ONLY"))
            connection.execute(text("SET LOCAL statement_timeout = '15000'"))
            rows = pd.read_sql(text("SELECT m.id, m.api_id, c.code AS league, h.name AS home_team, a.name AS away_team, m.utc_date, m.status, m.home_score, m.away_score FROM matches m JOIN competitions c ON c.id=m.competition_id JOIN teams h ON h.id=m.home_team_id JOIN teams a ON a.id=m.away_team_id"), connection)
            pred_counts = pd.read_sql(text("SELECT p.model_name, count(*) AS predictions, count(*) FILTER (WHERE p.predicted_at < m.utc_date) AS before_kickoff, count(*) FILTER (WHERE p.predicted_at >= m.utc_date) AS at_or_after_kickoff FROM predictions p JOIN matches m ON m.id=p.match_id GROUP BY p.model_name"), connection)
        resolver = HistoricalMatchModel.load()
        rows["utc_date"] = pd.to_datetime(rows.utc_date, errors="coerce")
        future_finished = rows[(rows.status == "FINISHED") & (rows.utc_date >= AS_OF + pd.Timedelta(days=1))]
        future_finished.to_csv(out / "database_future_finished.csv", index=False)
        missing_finished_scores = rows[(rows.status == "FINISHED") & (rows.home_score.isna() | rows.away_score.isna())]
        missing_finished_scores.to_csv(out / "database_finished_missing_scores.csv", index=False)
        upcoming = rows[(rows.utc_date >= AS_OF) & (rows.utc_date < AS_OF + pd.Timedelta(days=30)) & rows.status.isin(["SCHEDULED", "TIMED"])]
        mappings = []
        for league, part in rows.groupby("league"):
            for name in sorted(set(part.home_team) | set(part.away_team)):
                resolved, confidence = resolver._resolve_team(league, name)
                state = resolver.states.get(resolver._state_key(league, resolved))
                requested = normalise_team_name(name)
                requested = resolver.TEAM_ALIASES.get(requested, requested)
                candidates = resolver.known_teams.get(league, set())
                ties = sorted(candidate for candidate in candidates if np.isclose(SequenceMatcher(None, requested, candidate).ratio(), confidence))
                active = upcoming[upcoming.league == league]
                active_count = int(((active.home_team == name) | (active.away_team == name)).sum())
                mappings.append({"league": league, "provider_name": name, "resolved": resolved,
                                 "confidence": confidence, "supported": league in resolver.known_teams,
                                 "state_last_result": str(state.last_match_date) if state else None,
                                 "upcoming_30_day_fixtures": active_count, "best_match_ties": "|".join(ties)})
        mapping_frame = pd.DataFrame(mappings)
        mapping_frame.to_csv(out / "database_team_mappings.csv", index=False)
        db_fresh = []
        for league, part in rows.groupby("league"):
            finished = pd.to_datetime(part.loc[part.status == "FINISHED", "utc_date"], errors="coerce")
            latest = finished.max()
            db_fresh.append({"league": league, "fixtures": len(part), "latest_finished": str(latest),
                             "finished_after_artifact": int((finished > matches.match_date.max()).sum())})
        database = {"status": "read_only_success", "fixture_coverage": db_fresh,
                    "saved_predictions": pred_counts.to_dict("records"),
                    "finished_after_audit_day": len(future_finished), "finished_missing_scores": len(missing_finished_scores),
                    "status_counts": {str(key): int(value) for key, value in rows.status.value_counts(dropna=False).items()},
                    "mapping_counts": {"teams": len(mapping_frame), "supported_low_confidence": int(((mapping_frame.confidence < .8) & mapping_frame.supported).sum()),
                                       "supported_low_confidence_with_upcoming_fixtures": int(((mapping_frame.confidence < .8) & mapping_frame.supported & (mapping_frame.upcoming_30_day_fixtures > 0)).sum())}}
    except Exception as exc:
        database = {"status": "unavailable_or_query_failed", "error_type": type(exc).__name__}
    # Demonstrate that loaded final states are not point-in-time historical states.
    resolver = HistoricalMatchModel.load()
    sample = examples[examples.league == "PL"].iloc[-1]
    home, _ = resolver._resolve_team(sample.league, sample.home_team)
    away, _ = resolver._resolve_team(sample.league, sample.away_team)
    loaded_features = resolver._features(sample.league, home, away, sample.match_date.to_pydatetime())
    historical_difference = {key: {"prematch_snapshot": sample.features[key], "loaded_final_state": loaded_features[key]}
                             for key in sample.features if not np.isclose(sample.features[key], loaded_features[key])}
    report = {
        "audit_date": str(AS_OF.date()), "artifact_trained_at": str(artifact.get("trained_at")),
        "raw": {"files": len(file_checks), "rows": sum(f["rows"] for f in file_checks), "valid_matches": len(matches),
                "discarded_rows": sum(f.get("discarded_rows", 0) for f in file_checks), "duplicate_fixture_rows": len(duplicates),
                "negative_or_fractional_scores": int(((matches.home_goals < 0) | (matches.away_goals < 0) | (matches.home_goals % 1 != 0) | (matches.away_goals % 1 != 0)).sum()),
                "same_team_matches": int((matches.home_team.map(normalise_team_name) == matches.away_team.map(normalise_team_name)).sum()),
                "result_label_mismatches": int(matches.result_label_mismatch.sum()), "freshness": freshness},
        "features": {"snapshot_matches": len(examples), "snapshot_source_labels_match": True,
                     "missing_numeric_cells": int(numeric.isna().sum().sum()), "nonfinite_numeric_cells": int((~np.isfinite(numeric.to_numpy())).sum()),
                     "position_outside_current_season_team_count": int(position_bad.sum()),
                     "sample_historical_final_state_differences": historical_difference},
        "evaluation": {"source": str(prediction_path), "model": "fixed CatBoost classifier, historical 80% training split grouped by date; not website ensemble",
                       "overall": summarize(evaluation), "always_home_accuracy": float((evaluation.actual == 2).mean()),
                       "league": per_league, "outcome": per_outcome,
                       "confusion_matrix_away_draw_home": confusion_matrix(evaluation.actual, evaluation.predicted, labels=[0, 1, 2]).tolist(),
                       "predicted_class_counts": {str(key): int(value) for key, value in evaluation.predicted.value_counts().items()},
                       "premier_league_prior_top_six": group_scores(pl, "prior_top_six"),
                       "promoted": group_scores(evaluation, "involves_promoted_team"),
                       "confidence": group_scores(evaluation, "confidence_band")},
        "database": database,
        "limitations": ["Audit reuses historical evaluation rows, not fresh validation.", "Prior top six are reconstructed on-pitch standings, without disciplinary deductions.",
                        "Fixture CSV lacks unique provider IDs; alignment checks dates and labels in saved snapshot order.",
                        "Browser-local saved forecasts are not accessible from this audit.", "Website 50/25/25 ensemble has not been backtested by these classifier experiments."]}
    (out / "results.json").write_text(json.dumps(report, indent=2, default=str), encoding="utf-8")
    print(json.dumps(report, indent=2, default=str), flush=True)


if __name__ == "__main__":
    main()
