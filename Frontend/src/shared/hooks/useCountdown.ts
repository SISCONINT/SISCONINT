import { useEffect, useState } from "react";

/** Cuenta regresiva en segundos. `resetKey` reinicia aunque `seconds` no cambie. */
export function useCountdown(seconds: number | null, resetKey?: unknown) {
  const key = `${String(resetKey ?? "")}:${seconds ?? 0}`;
  const [state, setState] = useState<{ key: string; left: number }>({
    key,
    left: seconds ?? 0,
  });

  const left = state.key === key ? state.left : seconds ?? 0;

  useEffect(() => {
    if (!seconds) return;
    const id = setInterval(() => {
      setState((prev) => {
        if (prev.key !== key) return { key, left: Math.max(0, seconds - 1) };
        if (prev.left <= 1) {
          clearInterval(id);
          return { key, left: 0 };
        }
        return { key, left: prev.left - 1 };
      });
    }, 1000);
    return () => clearInterval(id);
  }, [seconds, key]);

  return left;
}

export const formatMmSs = (total: number) =>
  `${String(Math.floor(total / 60)).padStart(2, "0")}:${String(total % 60).padStart(2, "0")}`;
