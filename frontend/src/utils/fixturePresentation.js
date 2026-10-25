export function fixtureDate(value) {
  if (!value) return null;
  const utc = /^\d{4}-\d{2}-\d{2}T[\d:.]+$/.test(value) ? `${value}Z` : value;
  const date = new Date(utc);
  return Number.isNaN(date.getTime()) ? null : date;
}

export function kickoffLabel(value, options = {}) {
  const date = fixtureDate(value);
  return date
    ? date.toLocaleString(undefined, {
        weekday: "short",
        day: "numeric",
        month: "short",
        hour: "2-digit",
        minute: "2-digit",
        ...options,
      })
    : "Kick-off to be confirmed";
}

export function normaliseFixture(match) {
  if (!match) return null;
  return {
    ...match,
    home_team_name: match.home_team_name || match.home_team || match.home?.name,
    away_team_name: match.away_team_name || match.away_team || match.away?.name,
    home_team_crest:
      match.home_team_crest || match.home_crest || match.home?.crest,
    away_team_crest:
      match.away_team_crest || match.away_crest || match.away?.crest,
    home_team_id: match.home_team_id || match.home?.id,
    away_team_id: match.away_team_id || match.away?.id,
    competition_name: match.competition_name || match.competition,
  };
}
