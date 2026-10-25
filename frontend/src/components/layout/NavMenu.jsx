import { useEffect, useRef, useState } from "react";
import { NavLink, useLocation } from "react-router-dom";
import { FiMenu, FiX, FiChevronDown } from "react-icons/fi";
const primary = [
  ["/dashboard", "Matchday"],
  ["/matches", "Matches"],
  ["/predictions", "Predictions"],
  ["/your-matchday", "Your matchday"],
];
const more = [
  ["/fan-vs-model", "Fan vs model"],
  ["/confidence-explorer", "Confidence explorer"],
  ["/forecast-movement", "Forecast movement"],
  ["/following", "Following"],
  ["/prediction-tracker", "Prediction tracker"],
  ["/compare", "Compare clubs"],
  ["/competitions", "Leagues & cups"],
  ["/teams", "Clubs"],
  ["/players", "Players"],
  ["/news", "Football news"],
  ["/analytics", "Analytics"],
];
export default function NavMenu() {
  const [open, setOpen] = useState(false),
    [moreOpen, setMoreOpen] = useState(false);
  const root = useRef(null),
    location = useLocation();
  useEffect(() => {
    setOpen(false);
    setMoreOpen(false);
  }, [location.pathname, location.search]);
  useEffect(() => {
    const outside = (event) => {
      if (!root.current?.contains(event.target)) {
        setOpen(false);
        setMoreOpen(false);
      }
    };
    const escape = (event) => {
      if (event.key === "Escape") {
        setOpen(false);
        setMoreOpen(false);
        root.current?.querySelector("button")?.focus();
      }
    };
    document.addEventListener("pointerdown", outside);
    document.addEventListener("keydown", escape);
    return () => {
      document.removeEventListener("pointerdown", outside);
      document.removeEventListener("keydown", escape);
    };
  }, []);
  return (
    <div className="flood-navigation" ref={root}>
      <button
        className="flood-nav-toggle"
        type="button"
        aria-label={open ? "Close navigation" : "Open navigation"}
        aria-expanded={open}
        aria-controls="matchday-navigation"
        onClick={() => setOpen(!open)}
      >
        {open ? <FiX /> : <FiMenu />}
      </button>
      <div
        id="matchday-navigation"
        className={`flood-nav-links${open ? " is-open" : ""}`}
      >
        {primary.map(([to, label]) => (
          <NavLink key={to} to={to}>
            {label}
          </NavLink>
        ))}
        <div className="flood-more">
          <button
            type="button"
            onClick={() => setMoreOpen(!moreOpen)}
            aria-expanded={moreOpen}
            aria-controls="football-more-links"
          >
            Explore <FiChevronDown />
          </button>
          <div
            className={`flood-more-links${moreOpen ? " is-open" : ""}`}
            id="football-more-links"
          >
            {more.map(([to, label]) => (
              <NavLink key={to} to={to}>
                {label}
              </NavLink>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
