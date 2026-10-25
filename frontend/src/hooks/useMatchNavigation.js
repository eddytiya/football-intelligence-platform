import { useEffect, useRef, useState } from "react";

import {
    getLatestMatchDate,
    getNextMatch,
} from "../api/matchApi";
import { localDateKey, shiftMatchDate, statusForMatchDate } from "../utils/matchDateNavigation";
import { fixtureDate } from "../utils/fixturePresentation";

function useMatchNavigation(
    selectedStatus = "SCHEDULED",
    setSelectedStatus,
) {

    const [selectedDate, setSelectedDate] =
        useState("");

    const [loading, setLoading] =
        useState(true);

    const [error, setError] =
        useState(null);
    const preserveSelectedDate = useRef(false);

    // ==========================================
    // Load Initial Date
    // ==========================================

    useEffect(() => {
        // Action buttons can deliberately select a date before switching the
        // status. Do not immediately overwrite that selection with today.
        if (preserveSelectedDate.current) {
            preserveSelectedDate.current = false;
            return;
        }
        loadInitialDate();

    }, [selectedStatus]);

    const loadInitialDate = async () => {

        try {

            setLoading(true);
            setError(null);

            switch (selectedStatus) {

            case "SCHEDULED": {

                const today = localDateKey();

                setSelectedDate(today);
                break;

            }

            case "FINISHED":
            case "LIVE":
            case "IN_PLAY":
            case "PAUSED": {

                const response =
                    await getLatestMatchDate(
                        selectedStatus
                    );

                if (response?.date) {

                    setSelectedDate(
                        response.date
                    );

                }

                break;

            }

            default: {

                const today = localDateKey();

                setSelectedDate(today);

            }

            }

        } catch (err) {

            setError(err);

        } finally {

            setLoading(false);

        }

    };

    // ==========================================
    // Previous Match Day
    // ==========================================

    const goToPrevious = () => setCustomDate(shiftMatchDate(selectedDate || localDateKey(), -1));

    // ==========================================
    // Next Match Day
    // ==========================================

    const goToNext = () => setCustomDate(shiftMatchDate(selectedDate || localDateKey(), 1));

    // ==========================================
    // Today
    // ==========================================

    const goToToday = () => {

        setCustomDate(localDateKey());

    };

    const goToLatestForStatus = async (status) => {
        try {
            const response = await getLatestMatchDate(status);
            if (response?.date) {
                if (selectedStatus !== status) preserveSelectedDate.current = true;
                setSelectedDate(response.date);
                setSelectedStatus(status);
            }
        } catch (err) {
            console.error(err);
        }
    };

    const goToNearestScheduledDate = async () => {
        try {
            // `/matches/next` is ordered from the current moment, so this
            // always returns the closest upcoming fixture rather than the
            // final scheduled fixture of the season.
            const match = await getNextMatch();
            const date = fixtureDate(match?.utc_date);
            if (date) {
                if (selectedStatus !== "SCHEDULED") preserveSelectedDate.current = true;
                setSelectedDate(localDateKey(date));
                setSelectedStatus("SCHEDULED");
            }
        } catch (err) {
            console.error(err);
        }
    };

    // ==========================================
    // Custom Date
    // ==========================================

    const setCustomDate = (
        date,
    ) => {

        const status = statusForMatchDate(date);
        // A date-driven status change must not jump to the latest result date.
        if (selectedStatus !== status) preserveSelectedDate.current = true;
        setSelectedDate(date);
        setSelectedStatus(status);

    };

    return {

        selectedDate,

        loading,

        error,

        goToPrevious,

        goToNext,

        goToToday,

        goToLatestForStatus,

        goToNearestScheduledDate,

        setCustomDate,

    };

}

export default useMatchNavigation;
