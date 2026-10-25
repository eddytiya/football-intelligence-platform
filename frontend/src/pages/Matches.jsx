import { useEffect, useMemo, useState } from "react";
import { useSearchParams } from "react-router-dom";

import MainLayout from "../components/layout/MainLayout";
import "../styles/fan-features.css";
import FootballLoader from "../components/layout/FootballLoader";

import MatchFilters from "../components/matches/MatchFilters";
import DateSelector from "../components/matches/DateSelector";
import MatchList from "../components/matches/MatchList";

import useMatchNavigation from "../hooks/useMatchNavigation";
import useMatches from "../hooks/useMatches";
import { getCompetitionMatchweeks, getStandingsSummary } from "../api/matchApi";

function Matches() {

    const [urlSearchParams] = useSearchParams();

    const [searchQuery, setSearchQuery] = useState(() => urlSearchParams.get("team") || "");
    const [searchScope, setSearchScope] = useState("all");
    const [searchSort, setSearchSort] = useState("date");
    const [selectedMatchweek, setSelectedMatchweek] = useState("");
    const [matchweeks, setMatchweeks] = useState([]);
    const [selectedCompetitionId, setSelectedCompetitionId] = useState(null);
    const [showPredictions, setShowPredictions] = useState(false);
    const [standings, setStandings] = useState(null);
    const [favouritesOnly, setFavouritesOnly] = useState(false);

    const [
        selectedCompetition,
        setSelectedCompetition,
    ] = useState("");

    const [
        selectedStatus,
        setSelectedStatus,
    ] = useState("SCHEDULED");

    const {

        selectedDate,

        loading,

        error,

        goToPrevious,

        goToNext,

        goToToday,

        goToNearestScheduledDate,
        goToLatestForStatus,

        setCustomDate,

    } = useMatchNavigation(
        selectedStatus,
        setSelectedStatus,
    );

    const {
        matches,
        loading: matchesLoading,
        error: matchesError,
        lastUpdated,
    } = useMatches(
        null,
        selectedDate,
        selectedStatus,
        searchQuery,
        selectedCompetitionId,
        selectedMatchweek,
    );

    const availableCompetitions = useMemo(() => {
        const seen = new Map();

        matches.forEach((match) => {
            if (match.competition_code && match.competition_name) {
                seen.set(match.competition_code, {
                    id: match.competition_id,
                    code: match.competition_code,
                    name: match.competition_name,
                });
            }
        });

        return [...seen.values()].sort((a, b) =>
            a.name.localeCompare(b.name)
        );
    }, [matches]);

    const selectedCompetitionData = availableCompetitions.find(
        (competition) => competition.code === selectedCompetition,
    );

    useEffect(() => {
        setSelectedMatchweek("");
        setShowPredictions(false);
        setSelectedCompetitionId(selectedCompetitionData?.id || null);
        if (!selectedCompetitionData || searchQuery.trim().length >= 2) {
            setMatchweeks([]);
            return;
        }
        getCompetitionMatchweeks(selectedCompetitionData.id, selectedStatus)
            .then(setMatchweeks)
            .catch(() => setMatchweeks([]));
    }, [selectedCompetitionData?.id, selectedStatus, searchQuery]);

    useEffect(() => {
        if (!selectedCompetitionData || !selectedMatchweek) {
            setStandings(null);
            return;
        }
        getStandingsSummary(selectedCompetitionData.id).then(setStandings).catch(() => setStandings(null));
    }, [selectedCompetitionData?.id, selectedMatchweek]);

    useEffect(() => {
        if (
            selectedCompetition &&
            !availableCompetitions.some(
                (competition) =>
                    competition.code === selectedCompetition
            )
        ) {
            setSelectedCompetition("");
        }
    }, [availableCompetitions, selectedCompetition]);

    if (loading) {
        return (
            <MainLayout>
                <section className="matches-page">
                    <FootballLoader label="Loading matchday fixtures" />
                </section>
            </MainLayout>
        );
    }

    if (error) {
        return (
            <MainLayout>
                <section className="matches-page">
                    Error loading matches.
                </section>
            </MainLayout>
        );
    }

    return (
        <MainLayout>

            <section className="matches-page">

                <div className="matches-header">

                    <h1>Football Matches</h1>

                    <p>
                        Browse upcoming football fixtures,
                        generate AI predictions,
                        and explore match insights.
                    </p>
                    <span className="live-sync-status"><i />Live scores refresh automatically</span>

                </div>

                <MatchFilters
                    searchQuery={searchQuery}
                    setSearchQuery={setSearchQuery}
                    selectedCompetition={selectedCompetition}
                    setSelectedCompetition={setSelectedCompetition}
                    selectedStatus={selectedStatus}
                    setSelectedStatus={setSelectedStatus}
                    competitions={availableCompetitions}
                    searchScope={searchScope}
                    setSearchScope={setSearchScope}
                    searchSort={searchSort}
                    setSearchSort={setSearchSort}
                    matchweeks={matchweeks}
                    selectedMatchweek={selectedMatchweek}
                    setSelectedMatchweek={setSelectedMatchweek}
                    favouritesOnly={favouritesOnly}
                    setFavouritesOnly={setFavouritesOnly}
                    goToToday={goToToday}
                />

                {searchQuery.trim().length < 2 && !selectedMatchweek && <DateSelector
                    selectedDate={selectedDate}
                    setSelectedDate={setCustomDate}
                    goToPrevious={goToPrevious}
                    goToNext={goToNext}
                    goToToday={goToToday}
                    goToNearestScheduledDate={goToNearestScheduledDate}
                    goToLatestForStatus={goToLatestForStatus}
                />}

                <MatchList
                    searchQuery={searchQuery}
                    selectedCompetition={selectedCompetition}
                    selectedStatus={selectedStatus}
                    matches={matches}
                    loading={matchesLoading}
                    error={matchesError}
                    isSearchActive={searchQuery.trim().length >= 2}
                    searchScope={searchScope}
                    searchSort={searchSort}
                    lastUpdated={lastUpdated}
                    selectedMatchweek={selectedMatchweek}
                    selectedCompetitionData={selectedCompetitionData}
                    matchweeks={matchweeks}
                    setSelectedMatchweek={setSelectedMatchweek}
                    showPredictions={showPredictions}
                    setShowPredictions={setShowPredictions}
                    standings={standings}
                    favouritesOnly={favouritesOnly}
                />

            </section>

        </MainLayout>
    );
}

export default Matches;
