import { useEffect, useState } from "react";
import { Link } from "react-router-dom";

import MainLayout from "../components/layout/MainLayout";
import FootballLoader from "../components/layout/FootballLoader";
import {
  getAccountFavourites,
  removeAccountFavourite,
} from "../api/accountApi";
import { getTeamProfile } from "../api/teamApi";
import "./Following.css";
import { fixtureDate } from "../utils/fixturePresentation";

function Following() {
  const [clubs, setClubs] = useState(null);
  const [error, setError] = useState("");

  const load = () => {
    getAccountFavourites()
      .then((rows) => {
        const teamIds = rows
          .filter((row) => row.entity_type === "team")
          .map((row) => row.entity_id);
        if (!teamIds.length) {
          setClubs([]);
          return;
        }
        Promise.all(
          teamIds.map((id) => getTeamProfile(id).catch(() => null)),
        ).then((profiles) => {
          setClubs(profiles.filter(Boolean));
        });
      })
      .catch(() => {
        setClubs([]);
        setError("Your followed clubs are unavailable right now.");
      });
  };

  useEffect(load, []);

  const unfollow = (teamId) => {
    removeAccountFavourite("team", teamId)
      .then(() => {
        window.dispatchEvent(new Event("football-favourites-updated"));
        load();
      })
      .catch(() => {});
  };

  if (clubs === null)
    return (
      <MainLayout>
        <FootballLoader label="Loading your followed clubs" />
      </MainLayout>
    );

  return (
    <MainLayout>
      <section className="following-page">
        <header className="following-hero">
          <div>
            <span>Your matchday feed</span>
            <h1>Following</h1>
            <p>
              Updates for every club you follow — next fixture, last result and
              recent form, in one place.
            </p>
          </div>
          <div className="following-hero-stat">
            <b>{clubs.length}</b>
            <span>clubs followed</span>
          </div>
        </header>

        {error && <p className="following-empty">{error}</p>}

        {!clubs.length ? (
          <div className="following-empty">
            <p>You're not following any clubs yet.</p>
            <Link to="/teams">
              Star a club from Teams to see its updates here →
            </Link>
          </div>
        ) : (
          <div className="following-grid">
            {clubs.map((club) => {
              const next = club.upcoming_fixtures?.find((fixture) => {
                const date = fixtureDate(fixture.utc_date);
                return date && date.getTime() > Date.now();
              });
              const last = club.recent_results?.[0];
              return (
                <article className="following-card" key={club.id}>
                  <header>
                    {club.crest ? (
                      <img src={club.crest} alt="" />
                    ) : (
                      <b>{club.tla || club.name.slice(0, 2)}</b>
                    )}
                    <div>
                      <Link to={`/teams/${club.id}`}>
                        <strong>{club.name}</strong>
                      </Link>
                      <span>
                        {club.competitions
                          ?.map((item) => item.name)
                          .join(" · ") || "Tracked club"}
                      </span>
                    </div>
                    <button type="button" onClick={() => unfollow(club.id)}>
                      Unfollow
                    </button>
                  </header>
                  <div className="following-form">
                    {club.form?.length ? (
                      club.form.map((result, index) => (
                        <i
                          className={`team-form-${result}`}
                          key={`${result}-${index}`}
                        >
                          {result}
                        </i>
                      ))
                    ) : (
                      <small>Awaiting results</small>
                    )}
                  </div>
                  <div className="following-updates">
                    <div>
                      <span>Next fixture</span>
                      {next ? (
                        <strong>
                          {next.home_team} <i>vs</i> {next.away_team}
                          <small>
                            {new Date(next.utc_date).toLocaleDateString(
                              undefined,
                              { day: "numeric", month: "short" },
                            )}
                          </small>
                        </strong>
                      ) : (
                        <small>No scheduled fixture</small>
                      )}
                    </div>
                    <div>
                      <span>Last result</span>
                      {last ? (
                        <strong>
                          {last.home_team}{" "}
                          <i>
                            {last.home_score}–{last.away_score}
                          </i>{" "}
                          {last.away_team}
                          <small>
                            {new Date(last.utc_date).toLocaleDateString(
                              undefined,
                              { day: "numeric", month: "short" },
                            )}
                          </small>
                        </strong>
                      ) : (
                        <small>No completed results yet</small>
                      )}
                    </div>
                  </div>
                  <div className="following-footer">
                    <Link className="following-open" to={`/teams/${club.id}`}>
                      Open team centre <b>→</b>
                    </Link>
                    <Link
                      className="following-news"
                      to={`/news?club=${encodeURIComponent(club.name)}`}
                    >
                      Club news
                    </Link>
                  </div>
                </article>
              );
            })}
          </div>
        )}
      </section>
    </MainLayout>
  );
}

export default Following;
