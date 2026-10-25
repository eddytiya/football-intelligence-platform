import { useEffect, useState } from "react";
import { getMatch } from "../api/matchApi";
import {
  readForecastArchive,
  reconcileForecasts,
} from "../utils/forecastTracker";
export default function useForecastResults(refreshKey) {
  const [state, setState] = useState({ rows: [], loading: true });
  useEffect(() => {
    let active = true;
    const controller = new AbortController();
    setState((previous) => ({ ...previous, loading: true }));
    reconcileForecasts(readForecastArchive(), (id) =>
      getMatch(id, { signal: controller.signal, timeout: 12000 }),
    ).then((rows) => active && setState({ rows, loading: false }));
    return () => {
      active = false;
      controller.abort();
    };
  }, [refreshKey]);
  return state;
}
