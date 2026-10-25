import { useState } from "react";
import { Link } from "react-router-dom";
import MainLayout from "../components/layout/MainLayout";
import useForecastResults from "../hooks/useForecastResults";
import { calibrationBins } from "../utils/forecastEvidence";
import "../styles/fan-features.css";

const pct = (value) => (value == null ? "—" : `${(value * 100).toFixed(1)}%`);
export default function ConfidenceExplorer() {
  const [refresh, setRefresh] = useState(0),
    [mode, setMode] = useState("top"),
    [league, setLeague] = useState(""),
    [model, setModel] = useState("");
  const { rows, loading } = useForecastResults(refresh);
  const selected = rows.filter(
    (row) =>
      (!league || row.league === league) &&
      (!model || (row.model_version || "Unrecorded") === model),
  );
  const bins = calibrationBins(selected, mode);
  const count = bins.reduce((sum, bin) => sum + bin.count, 0),
    gap = count
      ? bins.reduce(
          (sum, bin) => sum + bin.count * Math.abs(bin.expected - bin.observed),
          0,
        ) / count
      : null;
  return (
    <MainLayout>
      <section className="fan-page">
        <header className="fan-page-heading">
          <div>
            <h1>Confidence explorer</h1>
            <p>When the model says 60%, how often does that outcome happen?</p>
          </div>
          <button
            className="flood-button subtle"
            disabled={loading}
            onClick={() => setRefresh((value) => value + 1)}
          >
            Refresh results
          </button>
        </header>
        <p className="fan-scope">
          Calibration of the earliest valid pre-match forecast saved per fixture
          in this browser. Completed results only. This personal, selected
          sample is not a full model evaluation; confidence is not measured
          accuracy.
        </p>
        <div className="fan-filters">
          <label>
            Outcome
            <select
              value={mode}
              onChange={(event) => setMode(event.target.value)}
            >
              <option value="top">Top-pick confidence</option>
              <option value="home">Home-win probability</option>
              <option value="draw">Draw probability</option>
              <option value="away">Away-win probability</option>
            </select>
          </label>
          <label>
            Competition
            <select
              value={league}
              onChange={(event) => setLeague(event.target.value)}
            >
              <option value="">All competitions</option>
              {[...new Set(rows.map((row) => row.league).filter(Boolean))]
                .sort()
                .map((name) => (
                  <option key={name}>{name}</option>
                ))}
            </select>
          </label>
          <label>
            Model version
            <select
              value={model}
              onChange={(event) => setModel(event.target.value)}
            >
              <option value="">All saved versions</option>
              {[
                ...new Set(
                  rows.map((row) => row.model_version || "Unrecorded"),
                ),
              ]
                .sort()
                .map((name) => (
                  <option key={name}>{name}</option>
                ))}
            </select>
          </label>
        </div>
        {loading ? (
          <p role="status">Checking saved forecasts and final results…</p>
        ) : count ? (
          <>
            <p className="fan-scope">
              <b>{count} completed forecasts</b> · Mean calibration gap (ECE):{" "}
              <b>{(gap * 100).toFixed(1)} percentage points</b>.{" "}
              {count < 100
                ? "Small sample: apparent gaps can be dominated by chance."
                : "Bin sizes and selection bias still affect this estimate."}{" "}
              {selected.filter((row) => row.state === "unavailable").length}{" "}
              results could not be checked.
            </p>
            <div className="evidence-plot">
              <svg
                viewBox="0 0 600 360"
                role="img"
                aria-label="Calibration plot: predicted probability on the horizontal axis, observed outcome frequency on the vertical axis. Exact values are in the table below."
              >
                <line
                  className="plot-axis"
                  x1="65"
                  y1="295"
                  x2="555"
                  y2="295"
                />
                <line className="plot-axis" x1="65" y1="295" x2="65" y2="30" />
                <line
                  className="plot-reference"
                  x1="65"
                  y1="295"
                  x2="555"
                  y2="30"
                />
                {[0, 0.5, 1].map((value) => (
                  <g key={value}>
                    <text x={65 + 490 * value} y="320" textAnchor="middle">
                      {value * 100}%
                    </text>
                    <text x="50" y={300 - 265 * value} textAnchor="end">
                      {value * 100}%
                    </text>
                  </g>
                ))}
                {bins
                  .filter((bin) => bin.count)
                  .map((bin) => (
                    <circle
                      key={bin.lower}
                      cx={65 + 490 * bin.expected}
                      cy={295 - 265 * bin.observed}
                      r={Math.min(13, 5 + Math.sqrt(bin.count))}
                    >
                      <title>{`${bin.count} forecasts: expected ${pct(bin.expected)}, observed ${pct(bin.observed)}`}</title>
                    </circle>
                  ))}
                <text x="310" y="350" textAnchor="middle">
                  Mean predicted probability
                </text>
                <text x="70" y="18">
                  Observed frequency
                </text>
              </svg>
              <p>
                Dashed line: perfect calibration. Dots above it happened more
                often than predicted; below it, less often. Larger dots contain
                more fixtures.
              </p>
            </div>
            <div className="fan-table-scroll">
              <table className="fan-table">
                <thead>
                  <tr>
                    <th>Probability band</th>
                    <th>Fixtures</th>
                    <th>Mean predicted</th>
                    <th>Observed frequency</th>
                    <th>Gap</th>
                  </tr>
                </thead>
                <tbody>
                  {bins.map((bin) => (
                    <tr key={bin.lower}>
                      <th>
                        {Math.round(bin.lower * 100)}–
                        {Math.round(bin.upper * 100)}%
                      </th>
                      <td>{bin.count}</td>
                      <td>{pct(bin.expected)}</td>
                      <td>{pct(bin.observed)}</td>
                      <td>
                        {bin.count
                          ? `${((bin.observed - bin.expected) * 100).toFixed(1)} pp`
                          : "—"}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </>
        ) : (
          <div className="fan-empty">
            <h2>Evidence comes after full time</h2>
            <p>
              No eligible completed forecasts match these filters. Open
              forecasts before kickoff, then return when results are recorded.
              We won’t substitute historical experiment scores for this sample.
            </p>
            <Link className="flood-button" to="/matches">
              Find a match
            </Link>
          </div>
        )}
        <details className="fan-method">
          <summary>How to read this analysis</summary>
          <p>
            Each fixture contributes once, using its earliest valid saved
            snapshot. Bands include the lower boundary and exclude the upper,
            except the final band includes 100%. Top-pick mode checks whether
            the highest-probability outcome happened; exact ties use home, draw,
            away order. Outcome-specific modes compare that outcome’s
            probability with its actual frequency.
          </p>
          <p>
            ECE is the sample-weighted mean absolute gap across these ten bands.
            It depends on banding and sample size. This descriptive view does
            not establish statistical significance, explain causes or
            automatically recalibrate the model. Pending, invalid and
            unavailable results are omitted.{" "}
            <Link to="/prediction-tracker">
              See individual records and scoring rules.
            </Link>
          </p>
        </details>
      </section>
    </MainLayout>
  );
}
