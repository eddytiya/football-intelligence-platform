import MatchDateGroup from "./MatchDateGroup";
import MatchweekOverview from "./MatchweekOverview";
import CalendarExport from "./CalendarExport";
import "./Matches.css";

function MatchList({
    searchQuery,
    selectedCompetition,
    selectedStatus,
    matches,
    loading,
    error,
    isSearchActive,
    searchScope,
    searchSort,
    lastUpdated,
    selectedMatchweek,
    selectedCompetitionData,
    matchweeks,
    setSelectedMatchweek,
    showPredictions,
    setShowPredictions,
    standings,
    favouritesOnly,
}) {
    if (loading) {
        return (
            <div className="match-list-skeleton" aria-label="Loading matches">
                {[1, 2, 3].map((item) => <div className="skeleton-competition" key={item}><i /><span /><span /><span /></div>)}
            </div>
        );
    }

    if (error) {
        return (
            <div className="match-list-error">
                {error.message}
            </div>
        );
    }

    // ===================================
    // Apply Filters
    // ===================================

    let filteredMatches = matches.filter((match) => {

        // Search Team

        const search = searchQuery
            .trim()
            .toLowerCase();

        const matchesSearch =

            search === "" ||

            match.home_team_name
                ?.toLowerCase()
                .includes(search) ||

            match.away_team_name
                ?.toLowerCase()
                .includes(search);

        // Competition

        const matchesCompetition =

            selectedCompetition === "" ||

            match.competition_code ===
            selectedCompetition;

        // Status

        const matchesStatus =

            selectedStatus === "" ||

            match.status ===
            selectedStatus;

        return (
            matchesSearch &&
            matchesCompetition &&
            matchesStatus
        );

    });

    if (favouritesOnly) {
        const favouriteIds = new Set(JSON.parse(localStorage.getItem("favouriteMatchIds") || "[]"));
        filteredMatches = filteredMatches.filter((match) => favouriteIds.has(match.id));
    }

    if (isSearchActive) {
        const search = searchQuery.trim().toLowerCase();
        if (searchScope === "home") {
            filteredMatches = filteredMatches.filter((match) => match.home_team_name?.toLowerCase().includes(search));
        } else if (searchScope === "away") {
            filteredMatches = filteredMatches.filter((match) => match.away_team_name?.toLowerCase().includes(search));
        }
        if (searchSort === "competition") {
            filteredMatches.sort((a, b) => (a.competition_name || "").localeCompare(b.competition_name || "") || new Date(a.utc_date) - new Date(b.utc_date));
        } else {
            filteredMatches.sort((a, b) => new Date(a.utc_date) - new Date(b.utc_date));
        }
        if (searchScope === "next5") filteredMatches = filteredMatches.slice(0, 5);
    }

    if (filteredMatches.length === 0) {
        return (
            <div className="match-list-empty">
                No matches found.
            </div>
        );
    }

    const searchTeam = isSearchActive
        ? filteredMatches.flatMap((match) => [
            { name: match.home_team_name, crest: match.home_team_crest },
            { name: match.away_team_name, crest: match.away_team_crest },
        ]).find((team) => team.name?.toLowerCase().includes(searchQuery.trim().toLowerCase()))
        : null;

    // ============================
    // Group by Date
    // ============================

    const groupedByDate = {};

    filteredMatches.forEach((match) => {

        const date = new Date(match.utc_date)
            .toLocaleDateString("en-GB", {
                weekday: "long",
                day: "numeric",
                month: "long",
                year: "numeric",
            });

        if (!groupedByDate[date]) {

            groupedByDate[date] = {};

        }

        if (
            !groupedByDate[date][match.competition_id]
        ) {

            groupedByDate[date][
                match.competition_id
            ] = {

                competition_id:
                    match.competition_id,

                competition_name:
                    match.competition_name,

                competition_emblem:
                    match.competition_emblem,

                matches: [],

            };

        }

        groupedByDate[date][
            match.competition_id
        ].matches.push(match);

    });

    return (

        <div className="match-list">
            <div className="fan-actions"><CalendarExport fixtures={filteredMatches} label="Export displayed upcoming fixtures" /><small>One-time .ics download. Schedule changes do not sync.</small></div>

            {selectedMatchweek && selectedCompetitionData && (
                <MatchweekOverview
                    competition={selectedCompetitionData}
                    matchweek={selectedMatchweek}
                    maxMatchweek={Math.max(...matchweeks)}
                    fixtureCount={filteredMatches.length}
                    onPrevious={() => setSelectedMatchweek(String(Number(selectedMatchweek) - 1))}
                    onNext={() => setSelectedMatchweek(String(Number(selectedMatchweek) + 1))}
                    showPredictions={showPredictions}
                    setShowPredictions={setShowPredictions}
                    standings={standings}
                />
            )}

            {isSearchActive && (
                <div className="team-search-hero">
                    <div className="team-search-identity">
                        {searchTeam?.crest && <img src={searchTeam.crest} alt="" />}
                        <div><span>Team fixture search</span><strong>{searchTeam?.name || searchQuery.trim()}</strong></div>
                    </div>
                    <div className="team-search-meta">
                        <strong>{filteredMatches.length}</strong><span>scheduled {filteredMatches.length === 1 ? "match" : "matches"}</span>
                        <small>{lastUpdated ? `Updated ${lastUpdated.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}` : "Updating…"}</small>
                    </div>
                </div>
            )}

            {Object.entries(groupedByDate).map(

                ([date, competitions]) => (

                    <MatchDateGroup

                        key={date}

                        date={date}

                        competitions={Object.values(
                            competitions
                        )}
                        hideCompetitionHeading={Boolean(selectedMatchweek)}
                        autoShowPrediction={showPredictions}

                    />

                )

            )}

        </div>

    );

}

export default MatchList;
