import { useState } from "react";
import { monochromeCrestFor } from "../utils/clubCrests";

// A real monochrome asset is selected explicitly; colour logos are never filtered.
export default function ClubCrest({
  name = "",
  src,
  variant = "colour",
  alt = "",
  className = "",
}) {
  const [failedSources, setFailedSources] = useState({});
  const monochrome = variant === "broadcast" ? monochromeCrestFor(name) : null;
  const source = [monochrome, src].find(
    (candidate) => candidate && !failedSources[candidate],
  );
  if (!source) {
    return (
      <span
        className={`dashboard-crest-fallback ${className}`}
        aria-hidden={alt ? undefined : true}
        role={alt ? "img" : undefined}
        aria-label={alt || undefined}
      >
        {name.trim().slice(0, 2).toUpperCase()}
      </span>
    );
  }
  return (
    <img
      className={`${className}${source === monochrome ? ' crest-monochrome' : ''}`.trim()}
      src={source}
      alt={alt}
      decoding="async"
      onError={() =>
        setFailedSources((failed) => ({ ...failed, [source]: true }))
      }
    />
  );
}
