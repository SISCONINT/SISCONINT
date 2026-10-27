import { useEffect, useState } from "react";

export function useDebounce<T>(value: T, delay = 400) {
  const [debounced, setDebounced] = useState(value);

  useEffect(() => {
    const id = setTimeout(() => setDebounced(value), delay);
    return () => clearTimeout(id); // si el valor cambia antes, cancela el temporizador
  }, [value, delay]);

  return debounced;
}