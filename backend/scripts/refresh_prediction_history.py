"""Refresh validated current-season provider history without importing database scores."""
import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.services.etl.prediction_history_sync import refresh_history

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--as-of", default=datetime.now(timezone.utc).date().isoformat())
    args = parser.parse_args()
    print(json.dumps(refresh_history(datetime.fromisoformat(args.as_of).replace(tzinfo=timezone.utc)), indent=2))
