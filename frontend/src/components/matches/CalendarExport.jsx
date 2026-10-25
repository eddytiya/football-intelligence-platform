import { FiCalendar } from "react-icons/fi";
import {
  buildCalendar,
  calendarFixtures,
  downloadText,
} from "../../utils/calendarExport";

export default function CalendarExport({
  fixtures = [],
  label = "Add to calendar",
}) {
  const count = calendarFixtures(fixtures).length;
  return (
    <button
      className="flood-button subtle calendar-export"
      type="button"
      disabled={!count}
      title={
        count
          ? "Download .ics for Apple Calendar, Google Calendar or Outlook. One-time export; schedule changes do not sync."
          : "No verified upcoming fixtures to export"
      }
      onClick={() => {
        const calendar = buildCalendar(fixtures);
        if (calendar)
          downloadText(
            calendar,
            "football-fixtures.ics",
            "text/calendar;charset=utf-8",
          );
      }}
    >
      <FiCalendar /> {label}
    </button>
  );
}
