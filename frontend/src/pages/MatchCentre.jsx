import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { FiArrowLeft, FiStar } from "react-icons/fi";
import MainLayout from "../components/layout/MainLayout";
import FootballLoader from "../components/layout/FootballLoader";
import BroadcastMatchup from "../components/matches/BroadcastMatchup";
import MatchCard from "../components/matches/MatchCard";
import CalendarExport from "../components/matches/CalendarExport";
import OutcomeProbabilities from "../components/predictions/OutcomeProbabilities";
import useFixtureForecast from "../hooks/useFixtureForecast";
import apiClient from "../api/apiClient";
import { getMatch, getMatchCentre } from "../api/matchApi";
import {
  getWatchlist,
  removeWatchlist,
  saveWatchlist,
} from "../api/accountApi";
import { kickoffLabel, normaliseFixture } from "../utils/fixturePresentation";
import "./MatchCentre.css";

function MatchExperience({ match, centre }) {
  const [isAdmin, setIsAdmin] = useState(null);
  const { forecast, loading, error, saved, review } = useFixtureForecast(match, { adminReview: isAdmin });
  useEffect(() => {
    let active = true;
    apiClient.get("/auth/me")
      .then(({ data: user }) => active && setIsAdmin(Boolean(user.is_admin)))
      .catch(() => active && setIsAdmin(false));
    return () => { active = false; };
  }, []);
  const [watched, setWatched] = useState(false),
    [watchError, setWatchError] = useState(""),
    [saving, setSaving] = useState(false);
  useEffect(() => {
    let active = true;
    getWatchlist()
      .then(
        (rows) =>
          active && setWatched(rows.some((row) => row.match_id === match.id)),
      )
      .catch(() => {});
    return () => {
      active = false;
    };
  }, [match.id]);
  const toggle = async () => {
    setSaving(true);
    try {
      await (watched ? removeWatchlist(match.id) : saveWatchlist(match.id));
      setWatched(!watched);
      try {
        const ids = new Set(
          JSON.parse(localStorage.getItem("favouriteMatchIds") || "[]"),
        );
        if (watched) ids.delete(match.id);
        else ids.add(match.id);
        localStorage.setItem("favouriteMatchIds", JSON.stringify([...ids]));
      } catch {
        /* The account watchlist remains saved when browser storage is unavailable. */
      }
      setWatchError("");
    } catch {
      setWatchError("Your watchlist could not be updated. Please try again.");
    } finally {
      setSaving(false);
    }
  };
  const events = centre?.events || [],
    lineups = centre?.lineups || [];
  return (
    <div className="flood-match-page">
      <header className="flood-match-top">
        <CalendarExport fixtures={[match]} />
        <Link to="/matches">
          <FiArrowLeft /> All matches
        </Link>
        <button
          type="button"
          className="flood-button subtle"
          aria-pressed={watched}
          disabled={saving}
          onClick={toggle}
        >
          <FiStar />
          {saving ? "Saving…" : watched ? "Saved to watchlist" : "Save fixture"}
        </button>
      </header>
      {watchError && (
        <p role="status" className="flood-alert">
          {watchError}
        </p>
      )}
      <BroadcastMatchup match={match} venue={centre?.venue} showLink={false} />
      <section className="flood-match-forecast">
        <div className="flood-section-heading">
          <div>
            <h1>{isAdmin && !["SCHEDULED", "TIMED"].includes(match.status) ? "Model review and outcome" : "How the match could go."}</h1>
            <p>{isAdmin ? "Admin view · past and upcoming match analysis." : "Three outcomes. One honest picture."}</p>
            <div className="fan-actions"><Link to={`/forecast-movement?match=${match.id}`}>Forecast movement</Link><Link to={`/fan-vs-model?match=${match.id}`}>Fan vs model</Link>{isAdmin && <Link to="/admin/predictions">Model performance review</Link>}</div>
          </div>
          <span className="flood-model-label">{review?.kind === "walk_forward" ? "Walk-forward backtest" : "Model estimate"}</span>
        </div>
        {loading ? (
          <p className="flood-empty" role="status">
            Building the probability breakdown from pre-match history…
          </p>
        ) : forecast ? (
          <>
            {review && <section className="flood-admin-result" aria-label="Admin prediction comparison">
              <p><strong>Predicted outcome: {forecast.predicted_outcome}</strong>{review.actual_outcome && <> · Actual: {review.home_score}–{review.away_score} ({review.actual_outcome}) · {review.correct ? "Correct" : "Incorrect"}</>}</p>
              <p>{forecast.review_note || (review.kind === "pre_match" ? "Saved before kick-off." : "Walk-forward backtest; reported separately from recorded pre-match accuracy.")}</p>
            </section>}
            <OutcomeProbabilities
              forecast={forecast}
              home={match.home_team_name}
              away={match.away_team_name}
            />
            <p className="flood-source">
              {forecast.generated_at || forecast.predicted_at
                ? `Forecast generated ${kickoffLabel(forecast.generated_at || forecast.predicted_at)}`
                : `Forecast retrieved ${kickoffLabel(forecast.received_at)}`}
              {forecast.model_version
                ? ` · Model ${forecast.model_version}`
                : ""}
            </p>
          </>
        ) : (
          <p className="flood-empty">{error}</p>
        )}
        {saved && (
          <details className="flood-saved-forecast">
            <summary>Your original pre-match forecast</summary>
            <p>
              Saved {kickoffLabel(saved.saved_at)} · {saved.predicted_outcome}
              {saved.likely_score
                ? ` · Likely score ${saved.likely_score}`
                : ""}
            </p>
            {saved.probabilities && (
              <OutcomeProbabilities
                forecast={{
                  home_win_probability: saved.probabilities.home,
                  draw_probability: saved.probabilities.draw,
                  away_win_probability: saved.probabilities.away,
                }}
                home={match.home_team_name}
                away={match.away_team_name}
                compact
              />
            )}
            <p>
              {["FINISHED", "AWARDED"].includes(match.status)
                ? `Final result: ${match.home_score ?? "—"} – ${match.away_score ?? "—"}`
                : "The original saved snapshot is preserved even if the model changes."}
            </p>
          </details>
        )}
      </section>
      {forecast && (
        <section className="flood-detailed-analysis">
          <h2>The story behind the forecast</h2>
          <MatchCard
            key={match.id}
            match={match}
            initialPrediction={forecast}
            analysisOnly
          />
        </section>
      )}
      <section className="flood-match-context">
        <article>
          <h2>Match timeline</h2>
          {events.length ? (
            events.map((event, index) => (
              <div className="flood-event" key={index}>
                <b>{event.minute}′</b>
                <div>
                  <strong>{event.type}</strong>
                  <p>
                    {event.player || event.detail || "Event detail unavailable"}
                    {event.assist ? ` · Assist: ${event.assist}` : ""}
                  </p>
                </div>
              </div>
            ))
          ) : (
            <p>Match events have not been supplied for this fixture.</p>
          )}
        </article>
        <article>
          <h2>Around the match</h2>
          <dl>
            <dt>Venue</dt>
            <dd>{centre?.venue?.name || "Not supplied"}</dd>
            <dt>Referee</dt>
            <dd>{centre?.referee || "Not supplied"}</dd>
            <dt>Weather</dt>
            <dd>
              {centre?.availability?.weather
                ? "Provider data available"
                : "Not supplied"}
            </dd>
            <dt>TV coverage</dt>
            <dd>
              {centre?.availability?.tv
                ? "Provider data available"
                : "Not supplied"}
            </dd>
          </dl>
          {centre?.provider_note && <small>{centre.provider_note}</small>}
        </article>
      </section>
      <section className="flood-lineups">
        <h2>Team sheets</h2>
        {lineups.length ? (
          <div className="lineup-columns">
            {[
              { id: match.home_team_id, name: match.home_team_name },
              { id: match.away_team_id, name: match.away_team_name },
            ].map((team) => (
              <article key={team.id}>
                <h3>{team.name}</h3>
                {lineups
                  .filter((entry) => entry.team_id === team.id)
                  .map((entry, index) => (
                    <p
                      key={index}
                      className={entry.starter ? "starter" : "bench"}
                    >
                      {entry.player}
                      {entry.captain ? " · Captain" : ""}
                      <small>{entry.position}</small>
                    </p>
                  ))}
              </article>
            ))}
          </div>
        ) : (
          <p>Confirmed lineups will appear when the provider supplies them.</p>
        )}
      </section>
    </div>
  );
}

export default function MatchCentre() {
  const { matchId } = useParams();
  const [state, setState] = useState({
    loading: true,
    match: null,
    centre: null,
    error: "",
  });
  useEffect(() => {
    let active = true;
    setState({ loading: true, match: null, centre: null, error: "" });
    Promise.allSettled([getMatch(matchId), getMatchCentre(matchId)]).then(
      ([base, context]) => {
        if (!active) return;
        const centre = context.status === "fulfilled" ? context.value : null;
        const match =
          base.status === "fulfilled"
            ? normaliseFixture(base.value)
            : normaliseFixture(centre?.match);
        setState({
          loading: false,
          match,
          centre,
          error: match
            ? ""
            : "This fixture could not be loaded. Return to matches and try another fixture.",
        });
      },
    );
    return () => {
      active = false;
    };
  }, [matchId]);
  return (
    <MainLayout>
      {state.loading ? (
        <FootballLoader label="Opening the match centre" />
      ) : state.match ? (
        <MatchExperience
          key={matchId}
          match={state.match}
          centre={state.centre}
        />
      ) : (
        <section className="flood-page-error">
          <h1>Fixture unavailable</h1>
          <p>{state.error}</p>
          <Link to="/matches">Back to matches</Link>
        </section>
      )}
    </MainLayout>
  );
}
