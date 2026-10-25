"""Refresh provider CSVs after validation; never import unverified database scores."""
from __future__ import annotations

import io
import json
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from uuid import uuid4
import httpx
import pandas as pd
from app.core.paths import DATA_DIR, REPORTS_DIR
from etl.historical.downloader import HistoricalDownloader


def validate_download(content, season, now):
    frame = pd.read_csv(io.BytesIO(content), low_memory=False)
    required = {"Date", "HomeTeam", "AwayTeam", "FTHG", "FTAG"}
    if not required.issubset(frame):
        raise ValueError("Provider response is missing required CSV columns")
    dates = pd.to_datetime(frame.Date, format="%d/%m/%Y", errors="coerce")
    missing = dates.isna()
    dates.loc[missing] = pd.to_datetime(frame.loc[missing, "Date"], format="%d/%m/%y", errors="coerce")
    hg, ag = (pd.to_numeric(frame[col], errors="coerce") for col in ("FTHG", "FTAG"))
    valid = dates.notna() & hg.notna() & ag.notna() & frame.HomeTeam.notna() & frame.AwayTeam.notna()
    if not valid.any():
        raise ValueError("No completed matches in provider response")
    valid_dates = dates[valid]
    if (valid_dates >= pd.Timestamp(now.date()) + pd.Timedelta(days=1)).any():
        raise ValueError("Provider CSV has completed results in the future")
    if (valid_dates < pd.Timestamp(season, 7, 1)).any() or (valid_dates >= pd.Timestamp(season + 1, 7, 1)).any():
        raise ValueError("Provider CSV dates do not match requested season")
    if ((hg[valid] < 0) | (ag[valid] < 0) | (hg[valid] % 1 != 0) | (ag[valid] % 1 != 0)).any():
        raise ValueError("Invalid scoreline in provider CSV")
    cleaned = frame.loc[valid].copy()
    if "FTR" in cleaned:
        actual = pd.Series("D", index=cleaned.index)
        actual.loc[hg[valid] > ag[valid]] = "H"
        actual.loc[hg[valid] < ag[valid]] = "A"
        if (cleaned.FTR.notna() & (cleaned.FTR != actual)).any():
            raise ValueError("Provider outcome label disagrees with full-time score")
    if cleaned.duplicated(["Date", "HomeTeam", "AwayTeam"]).any():
        raise ValueError("Duplicate provider fixtures")
    return cleaned, str(valid_dates.max().date())


def refresh_history(as_of=None):
    now = as_of or datetime.now(timezone.utc)
    season = now.year if now.month >= 7 else now.year - 1
    output = DATA_DIR / "raw" / "historical"
    output.mkdir(parents=True, exist_ok=True)
    def refresh(item):
        league, code = item
        url = f"{HistoricalDownloader.BASE_URL}/{str(season)[-2:]}{str(season + 1)[-2:]}/{code}.csv"
        try:
            response = httpx.get(url, timeout=20, follow_redirects=True)
            response.raise_for_status()
            frame, latest = validate_download(response.content, season, now)
            path = output / f"{league}_{season}.csv"
            if path.exists():
                prior = pd.read_csv(path, low_memory=False)
                if len(frame) < len(prior):
                    raise ValueError("Provider history shrank; retaining last accepted archive for review")
            # Keep a copy of the last accepted file for local recovery.
            if path.exists():
                import shutil
                backup = REPORTS_DIR / "data_repairs" / "history_backup"
                backup.mkdir(parents=True, exist_ok=True)
                shutil.copy2(path, backup / path.name)
            temporary = path.with_name(f".{path.name}.{uuid4().hex}.tmp")
            frame.to_csv(temporary, index=False)
            if not path.exists() or temporary.read_bytes() != path.read_bytes():
                temporary.replace(path)
            else:
                temporary.unlink()
            return {"league": league, "status": "refreshed", "matches": len(frame), "latest_result": latest, "url": url}
        except Exception as exc:
            return {"league": league, "status": "unavailable", "error_type": type(exc).__name__, "url": url}
    with ThreadPoolExecutor(max_workers=4) as pool:
        results = list(pool.map(refresh, HistoricalDownloader.LEAGUES.items()))
    report_dir = REPORTS_DIR / "data_repairs"
    report_dir.mkdir(parents=True, exist_ok=True)
    (report_dir / "history_refresh.json").write_text(json.dumps(results, indent=2), encoding="utf-8")
    return results
