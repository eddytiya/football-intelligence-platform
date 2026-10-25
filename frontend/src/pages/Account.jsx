import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import MainLayout from "../components/layout/MainLayout";
import {
  getAccountFavourites,
  getWatchlist,
  removeWatchlist,
} from "../api/accountApi";
import "./Account.css";

export default function Account() {
  const [account] = useState(
    () => JSON.parse(localStorage.getItem("football-auth") || "null")?.user,
  );
  const [watchlist, setWatchlist] = useState([]);
  const [favourites, setFavourites] = useState([]);
  const load = () => {
    getWatchlist()
      .then(setWatchlist)
      .catch(() => setWatchlist([]));
    getAccountFavourites()
      .then(setFavourites)
      .catch(() => setFavourites([]));
  };
  useEffect(load, []);
  return (
    <MainLayout>
      <main className="account-page">
        <section className="account-hero">
          <span>YOUR FOOTBALL ACCOUNT</span>
          <h1>{account?.email?.split("@")[0] || "Supporter"}'s watchlist</h1>
          <p>Your saved fixtures and clubs follow your signed-in account.</p>
        </section>
        <section className="account-kpis">
          <article>
            <b>{watchlist.length}</b>
            <span>Saved fixtures</span>
          </article>
          <article>
            <b>
              {
                favourites.filter((entry) => entry.entity_type === "team")
                  .length
              }
            </b>
            <span>Followed clubs</span>
          </article>
          <article>
            <b>
              {
                favourites.filter(
                  (entry) => entry.entity_type === "competition",
                ).length
              }
            </b>
            <span>Followed leagues</span>
          </article>
        </section>
        <section className="account-notice">
          <b>Fixture reminders</b>
          <p>
            Each saved fixture stores your reminder preference. Email and push
            delivery need a verified sender and notification provider, so they
            are not claimed as active here.
          </p>
        </section>
        <section className="account-section">
          <header>
            <span>YOUR WATCHLIST</span>
            <h2>Saved fixtures</h2>
          </header>
          <div className="watchlist-items">
            {watchlist.length ? (
              watchlist.map((fixture) => (
                <article key={fixture.match_id}>
                  <div>
                    <b>
                      {fixture.home_team} vs {fixture.away_team}
                    </b>
                    <small>
                      {fixture.utc_date
                        ? new Date(fixture.utc_date).toLocaleString()
                        : "Kick-off pending"}{" "}
                      · reminder {fixture.reminder_minutes}m
                    </small>
                  </div>
                  <div>
                    <Link to={`/matches/${fixture.match_id}`}>
                      Open match centre
                    </Link>
                    <button
                      type="button"
                      onClick={() =>
                        removeWatchlist(fixture.match_id).then(load)
                      }
                    >
                      Remove
                    </button>
                  </div>
                </article>
              ))
            ) : (
              <p>Use the star on a fixture to add it to your watchlist.</p>
            )}
          </div>
        </section>
      </main>
    </MainLayout>
  );
}
