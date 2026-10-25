import { fixtureDate, normaliseFixture } from "./fixturePresentation.js";

const escapeText = (value) =>
  String(value || "")
    .replace(/\\/g, "\\\\")
    .replace(/\r?\n/g, "\\n")
    .replace(/;/g, "\\;")
    .replace(/,/g, "\\,");
const utc = (date) =>
  date
    .toISOString()
    .replace(/[-:]/g, "")
    .replace(/\.\d{3}/, "");
// RFC 5545 limits physical lines to 75 UTF-8 octets, including continuation space.
function fold(line) {
  const encoder = new TextEncoder();
  let result = "",
    length = 0;
  for (const char of line) {
    const bytes = encoder.encode(char).length;
    if (length + bytes > 75) {
      result += "\r\n ";
      length = 1;
    }
    result += char;
    length += bytes;
  }
  return result;
}

export function calendarFixtures(fixtures, now = Date.now()) {
  return [
    ...new Map(
      fixtures
        .map(normaliseFixture)
        .filter(
          (match) =>
            match?.id &&
            fixtureDate(match.utc_date)?.getTime() > now &&
            ["SCHEDULED", "TIMED"].includes(match.status),
        )
        .map((match) => [String(match.id), match]),
    ).values(),
  ];
}

export function buildCalendar(fixtures, generatedAt = new Date()) {
  const eligible = calendarFixtures(fixtures, generatedAt.getTime());
  if (!eligible.length) return null;
  const lines = [
    "BEGIN:VCALENDAR",
    "VERSION:2.0",
    "PRODID:-//Football Intelligence Platform//Fixtures//EN",
    "CALSCALE:GREGORIAN",
    "METHOD:PUBLISH",
  ];
  for (const match of eligible) {
    lines.push(
      "BEGIN:VEVENT",
      `UID:fixture-${match.id}@football-intelligence.local`,
      `DTSTAMP:${utc(generatedAt)}`,
      `DTSTART:${utc(fixtureDate(match.utc_date))}`,
      `SUMMARY:${escapeText(`${match.home_team_name} vs ${match.away_team_name}`)}`,
      `DESCRIPTION:${escapeText(`${match.competition_name || "Football fixture"}. Kickoff as currently stored. This is a one-time export; check for schedule changes.`)}`,
    );
    if (match.venue) lines.push(`LOCATION:${escapeText(match.venue)}`);
    lines.push("STATUS:CONFIRMED", "END:VEVENT");
  }
  return [...lines, "END:VCALENDAR"].map(fold).join("\r\n") + "\r\n";
}

export function downloadText(contents, filename, type) {
  const url = URL.createObjectURL(new Blob([contents], { type }));
  const anchor = document.createElement("a");
  anchor.href = url;
  anchor.download = filename;
  anchor.click();
  window.setTimeout(() => URL.revokeObjectURL(url), 1000);
}
