"""Quarantine invalid result records, preserving a local restoration snapshot first."""
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from sqlalchemy import text
from app.core.paths import REPORTS_DIR
from app.db.database import engine
from app.services.matching.result_validation import result_issue


def main():
    now = datetime.now(timezone.utc)
    engine.echo = False
    output = REPORTS_DIR / "data_repairs"
    output.mkdir(exist_ok=True)
    backup = output / f"quarantine_{now.strftime('%Y%m%dT%H%M%S%fZ')}.json"
    with engine.begin() as connection:
        rows = connection.execute(text("SELECT id, api_id, utc_date, match_date, status, home_score, away_score FROM matches WHERE status != 'QUARANTINED' FOR UPDATE")).mappings()
        invalid = []
        undated_legacy = 0
        for row in rows:
            kickoff = row["utc_date"] or (datetime.combine(row["match_date"], datetime.min.time()) if row["match_date"] else None)
            # Existing CSV imports may have neither timestamp column populated.
            # Preserve those records for a separate source-identity review.
            if row["status"] == "FINISHED" and kickoff is None:
                undated_legacy += 1
                continue
            issue = result_issue(row["status"], kickoff, row["home_score"], row["away_score"], now)
            if issue:
                invalid.append({**dict(row), "reason": issue})
        # Write recovery data before the first database change. Retain score/date evidence.
        backup.write_text(json.dumps({"created_at": now.isoformat(), "records": invalid}, indent=2, default=str), encoding="utf-8")
        for row in invalid:
            connection.execute(text("UPDATE matches SET status='QUARANTINED' WHERE id=:id"), {"id": row["id"]})
    print(json.dumps({"quarantined": len(invalid), "undated_legacy_preserved": undated_legacy, "backup": str(backup),
                      "records": [{"id": r["id"], "reason": r["reason"]} for r in invalid[:25]]}, indent=2))


if __name__ == "__main__":
    main()
