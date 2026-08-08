// Copyright (c) 2026 Jayhawk314. PolyForm Noncommercial License 1.0.0 — see LICENSE.md.
import { useCallback, useEffect, useRef, useState } from "react";

export interface Resource<T> {
  data: T | null;
  loading: boolean;
  error: string;
  reload: () => void;
}

/** Load-and-track a read: distinguishes "still loading" from "loaded empty",
 *  which the old loader could not, and drops results from a dead mount. */
export function useResource<T>(load: () => Promise<T>): Resource<T> {
  const [data, setData] = useState<T | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const alive = useRef(true);

  useEffect(() => {
    alive.current = true;
    return () => { alive.current = false; };
  }, []);

  const reload = useCallback(() => {
    setLoading(true);
    load().then((value) => {
      if (!alive.current) return;
      setData(value);
      setError("");
      setLoading(false);
    }).catch((exc) => {
      if (!alive.current) return;
      setError(exc instanceof Error ? exc.message : String(exc));
      setLoading(false);
    });
  }, [load]);

  useEffect(() => { reload(); }, [reload]);

  return { data, loading, error, reload };
}
