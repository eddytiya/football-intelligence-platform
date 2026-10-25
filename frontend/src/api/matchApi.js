import apiClient from "./apiClient";
import { fixtureDate } from "../utils/fixturePresentation";

// ==========================================================
// Upcoming Matches
// ==========================================================

export const getUpcomingMatches = async (limit = null) => {
    const response = await apiClient.get("/matches/upcoming", {
        params: limit ? { limit } : {},
    });

    const upcoming = response.data.filter((match) => {
        const date = fixtureDate(match.utc_date);
        return date && date.getTime() > Date.now() && ["SCHEDULED", "TIMED"].includes(match.status);
    });
    return upcoming.sort((first, second) => fixtureDate(first.utc_date) - fixtureDate(second.utc_date));
};

// ==========================================================
// Next Match
// ==========================================================

export const getNextMatch = async () => {
    const matches = await getUpcomingMatches(50);
    return matches[0] || null;
};

// ==========================================================
// Today's Matches
// ==========================================================

export const getTodayMatches = async () => {
    const response = await apiClient.get("/matches/today");

    return response.data;
};

// ==========================================================
// Match Details
// ==========================================================

export const getMatch = async (matchId, options = {}) => {
    const response = await apiClient.get(
        `/matches/${matchId}`, options
    );

    return response.data;
};

// ==========================================================
// Competition Matches
// ==========================================================

export const getCompetitionMatches = async (
    competitionId,
    limit = null
) => {
    const response = await apiClient.get(
        `/matches/competition/${competitionId}`,
        {
            params: limit ? { limit } : {},
        }
    );

    return response.data;
};

// ==========================================================
// Matches By Date
// ==========================================================

export const getMatchesByDate = async (
    date,
    status = null,
) => {

    const response = await apiClient.get(
        `/matches/date/${date}`,
        {
            params: status
                ? {
                    status,
                }
                : {},
        }
    );

    return response.data;

};

// ==========================================================
// Latest Match Date
// ==========================================================

export const getLatestMatchDate = async (
    status = null,
) => {

    const response = await apiClient.get(
        "/matches/latest-date",
        {
            params: status
                ? {
                    status,
                }
                : {},
        }
    );

    return response.data;

};

// ==========================================================
// Previous Match Date
// ==========================================================

export const getPreviousMatchDate = async (
    currentDate,
    status = null,
) => {

    const response = await apiClient.get(
        "/matches/previous-date",
        {
            params: {
                current_date: currentDate,
                ...(status && { status }),
            },
        }
    );

    return response.data;

};

// ==========================================================
// Next Match Date
// ==========================================================

export const getNextMatchDate = async (
    currentDate,
    status = null,
) => {

    const response = await apiClient.get(
        "/matches/next-date",
        {
            params: {
                current_date: currentDate,
                ...(status && { status }),
            },
        }
    );

    return response.data;

};

export const getMatchCentre = async (matchId) => {
    const response = await apiClient.get(`/matches/${matchId}/centre`);
    return response.data;
};

export const searchMatchesByTeam = async (query, status = "SCHEDULED") => {
    const response = await apiClient.get("/matches/search", {
        params: { q: query, status },
    });
    return response.data;
};

export const getCompetitionMatchweeks = async (competitionId, status = "SCHEDULED") => {
    const response = await apiClient.get(`/matches/competition/${competitionId}/matchweeks`, { params: { status } });
    return response.data.matchweeks;
};

export const getMatchesByMatchweek = async (competitionId, matchweek, status = "SCHEDULED") => {
    const response = await apiClient.get(`/matches/competition/${competitionId}/matchweek/${matchweek}`, { params: { status } });
    return response.data;
};

export const getStandingsSummary = async (competitionId) => {
    const response = await apiClient.get(`/matches/competition/${competitionId}/standings-summary`);
    return response.data;
};

export const getCompetitionStandings = async (competitionId) => {
    const response = await apiClient.get(`/matches/competition/${competitionId}/standings`);
    return response.data;
};

export const getCompetitionIntelligence = async (competitionId) => {
    const response = await apiClient.get(`/matches/competition/${competitionId}/intelligence`);
    return response.data;
};

export const getCompetitionSeasonOutlook = async (competitionId) => {
    const response = await apiClient.get(`/matches/competition/${competitionId}/season-outlook`);
    return response.data;
};

// ==========================================================
// Calendar Match Counts
// ==========================================================

export const getMonthSummary = async (year, month, status = null) => {
    const response = await apiClient.get("/matches/month-summary", {
        params: { year, month, ...(status && { status }) },
    });
    return response.data;
};
