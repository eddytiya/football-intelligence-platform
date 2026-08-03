import "./Matches.css";

const MatchFilters = ({
    searchQuery,
    setSearchQuery,
    selectedCompetition,
    setSelectedCompetition,
    selectedStatus,
    setSelectedStatus,
    competitions,
    searchScope,
    setSearchScope,
    searchSort,
    setSearchSort,
    matchweeks,
    selectedMatchweek,
    setSelectedMatchweek,
    favouritesOnly,
    setFavouritesOnly,
    goToToday,
}) => {
    const handleReset = () => {
        setSearchQuery("");
        setSelectedCompetition("");
        setSelectedStatus("SCHEDULED");
        setSearchScope("all");
        setSearchSort("date");
        setSelectedMatchweek("");
        setFavouritesOnly(false);
    };

    return (
        <div className="match-filters">

            <div className="filter-group">

                <input
                    type="text"
                    placeholder="Search team..."
                    value={searchQuery}
                    onChange={(e) =>
                        setSearchQuery(e.target.value)
                    }
                />

            </div>

            <div className="filter-group">

                <select
                    value={selectedCompetition}
                    onChange={(e) =>
                        setSelectedCompetition(e.target.value)
                    }
                >

                    <option value="">
                        All Competitions
                    </option>

                    {competitions.map(
                        (competition) => (

                            <option
                                key={competition.code}
                                value={competition.code}
                            >
                                {competition.name}
                            </option>

                        )
                    )}

                </select>

            </div>

            {selectedCompetition && matchweeks.length > 0 && searchQuery.trim().length < 2 && (
                <div className="filter-group matchweek-filter">
                    <select value={selectedMatchweek} onChange={(event) => setSelectedMatchweek(event.target.value)}>
                        <option value="">All matchweeks</option>
                        {matchweeks.map((week) => <option key={week} value={week}>Matchweek {week}</option>)}
                    </select>
                </div>
            )}

            <div className="filter-group">

                <select
                    value={selectedStatus}
                    onChange={(e) =>
                        setSelectedStatus(e.target.value)
                    }
                >

                    <option value="SCHEDULED">
                        Scheduled
                    </option>

                    <option value="LIVE">
                        Live
                    </option>

                    <option value="FINISHED">
                        Finished
                    </option>

                </select>

            </div>

            <button
                className="reset-button"
                onClick={handleReset}
            >
                Reset Filters
            </button>

            <div className="match-quick-filters" aria-label="Quick match filters">
                <button type="button" onClick={() => { goToToday(); setSelectedStatus("SCHEDULED"); }}>Today</button>
                <button type="button" className={selectedStatus === "LIVE" ? "is-active" : ""} onClick={() => setSelectedStatus("LIVE")}>Live</button>
                <button type="button" className={favouritesOnly ? "is-active" : ""} onClick={() => setFavouritesOnly((value) => !value)}>★ Favourites</button>
            </div>

            {searchQuery.trim().length >= 2 && (
                <div className="search-tools">
                    <div className="search-scope-tabs" role="group" aria-label="Search fixture scope">
                        {[["all", "All"], ["home", "Home"], ["away", "Away"], ["next5", "Next 5"]].map(([value, label]) => (
                            <button type="button" key={value} className={searchScope === value ? "is-active" : ""} onClick={() => setSearchScope(value)}>{label}</button>
                        ))}
                    </div>
                    <select className="search-sort" value={searchSort} onChange={(event) => setSearchSort(event.target.value)} aria-label="Sort search results">
                        <option value="date">Nearest date</option>
                        <option value="competition">Competition</option>
                    </select>
                </div>
            )}

        </div>
    );
};

export default MatchFilters;
