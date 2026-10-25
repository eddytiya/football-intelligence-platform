"""Inventory optional statistics already on disk; no external requests or paid services."""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import pandas as pd
from app.core.paths import DATA_DIR, REPORTS_DIR


def main():
    rows = []
    for path in sorted((DATA_DIR / "raw" / "historical").glob("*.csv")):
        frame = pd.read_csv(path, low_memory=False)
        valid = frame.HomeTeam.notna() & frame.AwayTeam.notna() & pd.to_numeric(frame.FTHG, errors="coerce").notna() & pd.to_numeric(frame.FTAG, errors="coerce").notna()
        frame = frame[valid]
        league, season = path.stem.rsplit("_", 1)
        row = {"league": league, "season": int(season), "matches": len(frame)}
        for label, columns in (("shots", ["HS", "AS"]), ("shots_on_target", ["HST", "AST"]),
                               ("corners", ["HC", "AC"]), ("reported_xg", ["HxG", "AxG"])):
            row[label] = int(frame[columns].apply(pd.to_numeric, errors="coerce").notna().all(axis=1).sum()) if set(columns).issubset(frame) else 0
        rows.append(row)
    output = REPORTS_DIR / "form_feature_experiment"
    output.mkdir(exist_ok=True)
    table = pd.DataFrame(rows)
    table.to_csv(output / "free_data_inventory.csv", index=False)
    summary = table.groupby("league")[["matches", "shots", "shots_on_target", "corners", "reported_xg"]].sum()
    summary.to_csv(output / "free_data_coverage_by_league.csv")
    print(json.dumps(summary.to_dict("index"), indent=2))


if __name__ == "__main__":
    main()
