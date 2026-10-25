import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { FiArrowUpRight } from "react-icons/fi";
import Logo from "../components/layout/Logo";
import ThemeToggle, { useStadiumTheme } from "../components/layout/ThemeToggle";
import BroadcastMatchup from "../components/matches/BroadcastMatchup";
import { getDashboardSummary } from "../api/dashboardApi";
import { getNextMatch } from "../api/matchApi";
import "./Landing.css";

export default function Landing() {
  const { theme } = useStadiumTheme();
  const [summary, setSummary] = useState(null),
    [featured, setFeatured] = useState(null),
    [pending, setPending] = useState(true);
  useEffect(() => {
    let active = true;
    getDashboardSummary()
      .then((value) => active && setSummary(value))
      .catch(() => {});
    getNextMatch()
      .then((value) => active && setFeatured(value))
      .catch(() => {})
      .finally(() => active && setPending(false));
    return () => {
      active = false;
    };
  }, []);
  return (
    <main className="landing-page flood-landing">
      <header className="landing-topbar">
        <Link className="landing-brand" to="/">
          <Logo />
          <span>
            Football Intelligence Platform
            <small>Your matchday, understood.</small>
          </span>
        </Link>
        <nav aria-label="Account">
          <ThemeToggle />
          <Link className="landing-signin" to="/login">
            Sign in
          </Link>
          <Link className="flood-button" to="/register">
            Join the matchday <FiArrowUpRight />
          </Link>
        </nav>
      </header>
      <section className="flood-landing-hero">
        <div>
          <h1>
            Your football.
            <br />
            <span>{theme === 'light' ? 'In the daylight.' : 'Under the floodlights.'}</span>
          </h1>
          <p>
            The clubs you follow. The fixtures you’re waiting for. A clearer
            view of how the match could go.
          </p>
          <div className="flood-landing-actions">
            <Link className="flood-button" to="/register">
              Create free account <FiArrowUpRight />
            </Link>
            <Link className="flood-text-link" to="/login">
              Already a supporter? Sign in
            </Link>
          </div>
          <div className="flood-landing-proof">
            <strong>Football is unpredictable.</strong>
            <p>
              We show the home win, draw and away win estimates—along with the
              reasoning and the gaps in the data.
            </p>
          </div>
        </div>
        <div className="flood-landing-fixture">
          {pending ? (
            <div className="flood-empty" role="status">
              Finding the next stored fixture…
            </div>
          ) : (
            <BroadcastMatchup match={featured} showLink={false} />
          )}
          <Link to="/register">
            Make this your matchday <FiArrowUpRight />
          </Link>
        </div>
      </section>
      <section className="flood-landing-story">
        <div>
          <h2>Know your next match.</h2>
          <p>
            Find a fixture, explore form and expected goals, and see the
            estimated chance of every result. A forecast is a starting point for
            understanding football, never a promise.
          </p>
        </div>
        <div>
          <h2>Keep your clubs close.</h2>
          <p>
            Follow favourites, save a fixture watchlist and keep the original
            forecast alongside the final score. Your football, in one place.
          </p>
        </div>
      </section>
      <section className="flood-landing-close">
        <div>
          <h2>There’s always another match.</h2>
          <p>
            {summary?.total_predictions
              ? `${Number(summary.total_predictions).toLocaleString()} predictions recorded in the platform. `
              : ""}
            Build your own matchday hub. Free to use.
          </p>
        </div>
        <Link className="flood-button" to="/register">
          Find your football <FiArrowUpRight />
        </Link>
      </section>
      <footer className="flood-landing-footer">
        <span>Football Intelligence Platform · 2026</span>
        <span>Model estimates, not guarantees.</span>
        <a href="https://www.footylogos.com/">Crest assets: FootyLogos</a>
      </footer>
    </main>
  );
}
