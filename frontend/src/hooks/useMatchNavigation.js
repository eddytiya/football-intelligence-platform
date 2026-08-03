import { useEffect, useRef, useState } from "react";

import {
    getLatestMatchDate,
    getNextMatch,
    getNextMatchDate,
    getPreviousMatchDate,
} from "../api/matchApi";

function useMatchNavigation(
    selectedStatus = "SCHEDULED",
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

                const today = new Date()
                    .toISOString()
                    .split("T")[0];

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

                const today = new Date()
                    .toISOString()
                    .split("T")[0];

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

    const goToPrevious = async () => {

        try {

            const response =
                await getPreviousMatchDate(
                    selectedDate,
                    selectedStatus,
                );

            if (response?.date) {

                setSelectedDate(
                    response.date
                );

            }

        } catch (err) {

            console.error(err);

        }

    };

    // ==========================================
    // Next Match Day
    // ==========================================

    const goToNext = async () => {

        try {

            const response =
                await getNextMatchDate(
                    selectedDate,
                    selectedStatus,
                );

            if (response?.date) {

                setSelectedDate(
                    response.date
                );

            }

        } catch (err) {

            console.error(err);

        }

    };

    // ==========================================
    // Today
    // ==========================================

    const goToToday = () => {

        const today = new Date()
            .toISOString()
            .split("T")[0];

        setSelectedDate(today);

    };

    const goToLatestForStatus = async (status) => {
        try {
            const response = await getLatestMatchDate(status);
            if (response?.date) {
                preserveSelectedDate.current = true;
                setSelectedDate(response.date);
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
            if (match?.utc_date) {
                preserveSelectedDate.current = true;
                setSelectedDate(match.utc_date.slice(0, 10));
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

        setSelectedDate(date);

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
