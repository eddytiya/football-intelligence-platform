"""Refresh provider fixtures through a local calendar date, with an audit trail."""
import argparse
from collections import Counter
from datetime import date, datetime, time, timedelta, timezone
import json
from pathlib import Path
import sys
from zoneinfo import ZoneInfo

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sqlalchemy import func
from app.db.database import engine
from app.db.session import SessionLocal
from app.models.match import Match
from app.models.team import Team
from app.models.season import Season
from app.models.competition import Competition
from app.services.football_api import FootballAPIClient
from app.services.matching.result_validation import validate_provider_match

FIELDS = ('id', 'api_id', 'competition_id', 'season_id', 'home_team_id', 'away_team_id',
          'utc_date', 'match_date', 'kick_off', 'status', 'match_week', 'stage', 'home_score', 'away_score')


def snapshot(match):
    return {key: getattr(match, key) for key in FIELDS}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--until', type=date.fromisoformat)
    parser.add_argument('--start', type=date.fromisoformat)
    args = parser.parse_args()
    local_today = datetime.now(ZoneInfo('Asia/Kolkata')).date()
    until = args.until or local_today
    if until > local_today:
        parser.error('The result refresh cannot extend beyond today')
    cutoff = datetime.combine(until + timedelta(days=1), time.min, ZoneInfo('Asia/Kolkata')).astimezone(timezone.utc)
    engine.echo = False
    report_dir = Path(__file__).resolve().parents[1] / 'reports/latest_results' / datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')
    report_dir.mkdir(parents=True, exist_ok=True)
    client = FootballAPIClient()
    client.request_delay = 7  # Stay below the free-tier request budget.
    counts = Counter()
    issues = []
    changes = []
    seen = set()
    with SessionLocal() as db:
        numeric_provider_id = Match.api_id.op('~')('^[0-9]+$')
        oldest = db.query(func.min(Match.utc_date)).filter(numeric_provider_id,
            Match.status.in_(['SCHEDULED', 'TIMED', 'IN_PLAY', 'PAUSED']),
            Match.utc_date < cutoff.replace(tzinfo=None)).scalar()
        start = args.start or (oldest.date() if oldest else until - timedelta(days=7))
        if start > until:
            parser.error('Start date must not be after the end date')
        teams = {t.api_id: t.id for t in db.query(Team).filter(Team.api_id.isnot(None))}
        seasons = {s.api_id: s for s in db.query(Season).filter(Season.api_id.isnot(None))}
        competitions = {c.api_id: c.id for c in db.query(Competition).filter(Competition.api_id.isnot(None))}
        existing = {m.api_id: m for m in db.query(Match).filter(numeric_provider_id)}
        print(f'Refreshing {start} through {until} (Asia/Kolkata)', flush=True)
        end = until + timedelta(days=1)
        while end > start:
            begin = max(start, end - timedelta(days=9))
            label = f'{begin}_{end}'
            payload = client.get('/matches', params={'dateFrom': begin.isoformat(), 'dateTo': end.isoformat()})
            if payload is None:
                counts['failed_windows'] += 1
                issues.append({'window': label, 'reason': 'Provider did not return data'})
                end = begin
                continue
            (report_dir / f'provider_{label}.json').write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding='utf8')
            batch_changes = []
            for item in payload.get('matches', []):
                api_id = str(item.get('id'))
                if api_id in seen:
                    continue
                seen.add(api_id)
                counts['received'] += 1
                try:
                    validate_provider_match(item)
                    kickoff = datetime.fromisoformat(item['utcDate'].replace('Z', '+00:00')).astimezone(timezone.utc)
                    if kickoff >= cutoff:
                        counts['outside_local_date'] += 1
                        continue
                    comp = competitions.get(item['competition']['id'])
                    season = seasons.get(item['season']['id'])
                    home = teams.get(item['homeTeam']['id'])
                    away = teams.get(item['awayTeam']['id'])
                    if None in (comp, season, home, away):
                        raise ValueError('Missing local competition, season or team mapping')
                    if season.competition_id != comp:
                        raise ValueError('Season and competition identity mismatch')
                    match = existing.get(api_id)
                    if match is not None and (match.competition_id, match.home_team_id, match.away_team_id) != (comp, home, away):
                        raise ValueError('Provider match ID belongs to a different stored fixture')
                    if match is not None and match.status == 'QUARANTINED':
                        raise ValueError('Existing record is quarantined; manual review required')
                    before = snapshot(match) if match is not None else None
                    if match is None:
                        duplicate = db.query(Match.id).filter(Match.competition_id == comp,
                            Match.home_team_id == home, Match.away_team_id == away,
                            Match.utc_date == kickoff.replace(tzinfo=None)).first()
                        if duplicate:
                            raise ValueError('Same fixture already exists under another source ID')
                        match = Match(api_id=api_id, competition_id=comp, season_id=season.id,
                                      home_team_id=home, away_team_id=away)
                    scores = (item.get('score') or {}).get('fullTime') or {}
                    values = {'utc_date': kickoff.replace(tzinfo=None), 'match_date': kickoff.date(),
                              'kick_off': kickoff.time().replace(tzinfo=None), 'status': item['status'],
                              'match_week': item.get('matchday'), 'stage': item.get('stage'),
                              'home_score': scores.get('home'), 'away_score': scores.get('away')}
                    if before is not None and all(before.get(key) == value for key, value in values.items()):
                        counts['unchanged'] += 1
                        continue
                    for key, value in values.items():
                        setattr(match, key, value)
                    if before is None:
                        db.add(match)
                        existing[api_id] = match
                    batch_changes.append({'api_id': api_id, 'before': before, 'after': snapshot(match)})
                except (ValueError, KeyError, TypeError) as error:
                    counts['rejected'] += 1
                    issues.append({'api_id': api_id, 'reason': str(error)})
            # Save the before/after trail before committing any mutation.
            (report_dir / f'changes_{label}.json').write_text(json.dumps(batch_changes, default=str, indent=2), encoding='utf8')
            db.commit()
            for change in batch_changes:
                counts['created' if change['before'] is None else 'updated'] += 1
                if change['after']['status'] == 'FINISHED':
                    counts['finished_results_saved'] += 1
            changes.extend(batch_changes)
            print(f'{label}: {len(payload.get("matches", []))} received; {len(batch_changes)} saved', flush=True)
            end = begin
    report = {'start': str(start), 'until': str(until), 'completed_at': datetime.now(timezone.utc).isoformat(),
              'counts': dict(counts), 'issues': issues, 'report_directory': str(report_dir)}
    (report_dir / 'summary.json').write_text(json.dumps(report, indent=2), encoding='utf8')
    print(json.dumps(report, indent=2), flush=True)


if __name__ == '__main__':
    main()
