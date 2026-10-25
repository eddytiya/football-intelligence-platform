export default function OutcomeProbabilities({
  forecast,
  home,
  away,
  compact = false,
}) {
  const values = [
    forecast?.home_win_probability,
    forecast?.draw_probability,
    forecast?.away_win_probability,
  ];
  if (
    !values.every(
      (value) =>
        typeof value === "number" &&
        Number.isFinite(value) &&
        value >= 0 &&
        value <= 1,
    ) ||
    Math.abs(values.reduce((a, b) => a + b, 0) - 1) > 0.02
  )
    return (
      <p className="flood-empty">
        A verified probability breakdown is unavailable for this fixture.
      </p>
    );
  const maximum = Math.max(...values);
  const leaders = values.flatMap((value, index) =>
    Math.abs(value - maximum) < 0.00001 ? [index] : [],
  );
  const labels = [home || "Home win", "Draw", away || "Away win"];
  return (
    <div className={`flood-outcomes${compact ? " compact" : ""}`}>
      <div className="flood-outcome-numbers">
        {values.map((value, index) => (
          <div key={index}>
            <span>
              {labels[index]}
              {index === 1 ? "" : " win"}
            </span>
            <strong className={leaders.includes(index) ? "leading" : ""}>
              {(value * 100).toFixed(1)}
              <small>%</small>
            </strong>
          </div>
        ))}
      </div>
      <div className="flood-probability-bar" aria-hidden="true">
        {values.map((value, index) => (
          <i key={index} style={{ width: `${value * 100}%` }} />
        ))}
      </div>
      <p>
        {leaders.length > 1
          ? "The model estimates a balanced contest, with no single leading outcome."
          : `${leaders[0] === 1 ? "A draw has" : `${labels[leaders[0]]} have`} the largest individual estimated chance.${maximum < 0.5 ? " The other two outcomes combined remain more likely." : ""}`}
      </p>
      {!compact && (
        <small>
          Model estimates, not guarantees. Probabilities are not a measure of
          historical accuracy.
        </small>
      )}
    </div>
  );
}
