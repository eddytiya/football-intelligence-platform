import { useEffect, useState } from "react";

import {
    getUpcomingMatches,
    getMatchesByDate,
    searchMatchesByTeam,
    getMatchesByMatchweek,
} from "../api/matchApi";

export default function useMatches(
    limit = null,
    selectedDate = null,
    selectedStatus = "SCHEDULED",
    searchQuery = "",
    selectedCompetitionId = null,
    selectedMatchweek = "",
) {

    const [matches, setMatches] = useState([]);

    const [loading, setLoading] = useState(true);

    const [error, setError] = useState(null);
    const [lastUpdated, setLastUpdated] = useState(null);

    useEffect(() => {

        let isActive = true;

        async function loadMatches(showLoading = true) {

            try {

                if (showLoading) setLoading(true);

                setError(null);

                let data;

                if (selectedCompetitionId && selectedMatchweek) {
                    data = await getMatchesByMatchweek(selectedCompetitionId, selectedMatchweek, selectedStatus);
                } else if (searchQuery.trim().length >= 2) {
                    data = await searchMatchesByTeam(searchQuery.trim(), selectedStatus);
                } else if (selectedDate) {

                    data =
                        await getMatchesByDate(
                            selectedDate,
                            selectedStatus,
                        );

                } else {

                    data =
                        await getUpcomingMatches(
                            limit
                        );

                }

                if (isActive) {
                    setMatches(data);
                    setLastUpdated(new Date());
                }

            } catch (err) {

                if (isActive) setError(err);

            } finally {

                if (isActive && showLoading) setLoading(false);

            }

        }

        loadMatches();
        // Keep visible live/final scores current without interrupting the UI.
        const refreshTimer = window.setInterval(() => loadMatches(false), 60_000);

        return () => {
            isActive = false;
            window.clearInterval(refreshTimer);
        };

    }, [
        limit,
        selectedDate,
        selectedStatus,
        searchQuery,
        selectedCompetitionId,
        selectedMatchweek,
    ]);

    return {
        matches,
        loading,
        error,
        lastUpdated,
    };

}
