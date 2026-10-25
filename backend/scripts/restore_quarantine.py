"""Restore statuses from a specific quarantine backup without overwriting later provider updates."""
import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from sqlalchemy import text
from app.db.database import engine


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("backup", type=Path)
    args = parser.parse_args()
    rows = json.loads(args.backup.read_text(encoding="utf-8"))["records"]
    engine.echo = False
    with engine.begin() as connection:
        result = connection.execute(text("UPDATE matches SET status=:status WHERE id=:id AND status='QUARANTINED'"),
                                    [{"id": row["id"], "status": row["status"]} for row in rows]) if rows else None
    print(json.dumps({"restored": result.rowcount if result else 0}))


if __name__ == "__main__":
    main()
