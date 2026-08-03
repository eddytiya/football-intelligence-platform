import { useEffect, useMemo, useState } from "react";

import { getMonthSummary } from "../../api/matchApi";
import "./Matches.css";

const WEEKDAYS = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"];

const toDateKey = (date) => [
    date.getFullYear(),
    String(date.getMonth() + 1).padStart(2, "0"),
    String(date.getDate()).padStart(2, "0"),
].join("-");

const dateFromKey = (dateKey) => {
    const [year, month, day] = dateKey.split("-").map(Number);
    return new Date(year, month - 1, day);
};

function DateSelector({
    selectedDate,
    setSelectedDate,
    goToPrevious,
    goToNext,
    goToToday,
    goToNearestScheduledDate,
    setSelectedStatus,
    selectedStatus,
}) {
    const currentDate = selectedDate ? dateFromKey(selectedDate) : new Date();
    const [isCalendarOpen, setIsCalendarOpen] = useState(false);
    const [visibleMonth, setVisibleMonth] = useState(
        new Date(currentDate.getFullYear(), currentDate.getMonth(), 1),
    );
    const [matchCounts, setMatchCounts] = useState({});

    useEffect(() => {
        if (selectedDate) {
            const date = dateFromKey(selectedDate);
            setVisibleMonth(new Date(date.getFullYear(), date.getMonth(), 1));
        }
    }, [selectedDate]);

    useEffect(() => {
        getMonthSummary(visibleMonth.getFullYear(), visibleMonth.getMonth() + 1, selectedStatus)
            .then((summary) => setMatchCounts(summary.days || {}))
            .catch(() => setMatchCounts({}));
    }, [visibleMonth, selectedStatus]);

    const calendarDays = useMemo(() => {
        const firstDay = new Date(visibleMonth.getFullYear(), visibleMonth.getMonth(), 1);
        const daysInMonth = new Date(visibleMonth.getFullYear(), visibleMonth.getMonth() + 1, 0).getDate();

        return [
            ...Array(firstDay.getDay()).fill(null),
            ...Array.from({ length: daysInMonth }, (_, index) => index + 1),
        ];
    }, [visibleMonth]);

    const formattedDate = currentDate.toLocaleDateString("en-GB", {
        weekday: "long",
        day: "numeric",
        month: "long",
        year: "numeric",
    });
    const monthLabel = visibleMonth.toLocaleDateString("en-GB", {
        month: "long",
        year: "numeric",
    });
    const todayKey = toDateKey(new Date());

    const changeMonth = (offset) => {
        setVisibleMonth((month) => new Date(
            month.getFullYear(),
            month.getMonth() + offset,
            1,
        ));
    };

    return (
        <section className="date-selector" aria-label="Choose match date">
            <div className="date-selector-summary">
                <button type="button" className="date-nav-btn" onClick={goToPrevious} aria-label="Previous match day">‹</button>
                <div className="selected-date">
                    <p className="date-selector-label">Selected date</p>
                    <h3>{formattedDate}</h3>
                    <button
                        type="button"
                        className="change-date-btn"
                        onClick={() => setIsCalendarOpen((isOpen) => !isOpen)}
                        aria-expanded={isCalendarOpen}
                        aria-controls="match-date-calendar"
                    >
                        {isCalendarOpen ? "Close calendar" : "Change date"}
                    </button>
                </div>
                <button type="button" className="date-nav-btn" onClick={goToNext} aria-label="Next match day">›</button>
            </div>

            {isCalendarOpen && (
                <div id="match-date-calendar" className="calendar" role="group" aria-label="Match calendar">
                    <div className="calendar-header">
                        <button type="button" className="calendar-month-btn" onClick={() => changeMonth(-1)} aria-label="Previous month">‹</button>
                        <h4>{monthLabel}</h4>
                        <button type="button" className="calendar-month-btn" onClick={() => changeMonth(1)} aria-label="Next month">›</button>
                    </div>
                    <div className="calendar-weekdays" aria-hidden="true">
                        {WEEKDAYS.map((weekday) => <span key={weekday}>{weekday}</span>)}
                    </div>
                    <div className="calendar-days">
                        {calendarDays.map((day, index) => {
                            if (day === null) {
                                return <span className="calendar-day-empty" key={`empty-${index}`} />;
                            }

                            const dateKey = toDateKey(new Date(
                                visibleMonth.getFullYear(), visibleMonth.getMonth(), day,
                            ));
                            const isSelected = dateKey === selectedDate;
                            const matchCount = matchCounts[dateKey];

                            return (
                                <button
                                    type="button"
                                    key={dateKey}
                                    className={`calendar-day${isSelected ? " is-selected" : ""}${dateKey === todayKey ? " is-today" : ""}${matchCount ? " has-matches" : ""}`}
                                    onClick={() => {
                                        setSelectedDate(dateKey);
                                        setIsCalendarOpen(false);
                                    }}
                                    aria-pressed={isSelected}
                                    aria-label={`Show matches for ${dateFromKey(dateKey).toLocaleDateString("en-GB", { day: "numeric", month: "long", year: "numeric" })}`}
                                >
                                    {day}
                                    {matchCount && <small className="calendar-match-count">{matchCount}</small>}
                                </button>
                            );
                        })}
                    </div>
                </div>
            )}

            <div className="date-actions">
                <button type="button" className="date-action-btn" onClick={goToToday}>Today</button>
                <button type="button" className="date-action-btn" onClick={async () => {
                    await goToNearestScheduledDate();
                    setSelectedStatus("SCHEDULED");
                }}>Latest Fixtures</button>
                <button type="button" className="date-action-btn" onClick={() => setSelectedStatus("FINISHED")}>Latest Results</button>
            </div>
        </section>
    );
}

export default DateSelector;
