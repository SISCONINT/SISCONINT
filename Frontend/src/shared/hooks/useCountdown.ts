import { useEffect, useState } from "react";

/** Cuenta regresiva en segundos. `resetKey` reinicia aunque `seconds` no cambie. */
export function useCountdown(seconds: number | null, resetKey?: unknown) {
  const [left, setLeft] = useState(seconds ?? 0);

  useEffect(() => {
    setLeft(seconds ?? 0);
    if (!seconds) return;
    const id = setInterval(() => {
      setLeft((s) => {
        if (s <= 1) { clearInterval(id); return 0; }
        return s - 1;
      });
    }, 1000);
    return () => clearInterval(id);
  }, [seconds, resetKey]);

  return left;
}

export const formatMmSs = (total: number) =>
  `${String(Math.floor(total / 60)).padStart(2, "0")}:${String(total % 60).padStart(2, "0")}`;