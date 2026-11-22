import { useCallback, useState } from "react";

export { useDebounce } from "./useDebounce";
export { useCountdown } from "./useCountdown";

/** Estado abierto/cerrado para modales y paneles. */
export function useDisclosure(initial = false) {
  const [open, setOpen] = useState(initial);
  const onOpen = useCallback(() => setOpen(true), []);
  const onClose = useCallback(() => setOpen(false), []);
  const onToggle = useCallback(() => setOpen((value) => !value), []);
  return { open, onOpen, onClose, onToggle };
}

/** Estado de un formulario controlado con helper para cambios parciales. */
export function useFormState<T extends Record<string, unknown>>(initial: T) {
  const [values, setValues] = useState<T>(initial);
  const setField = useCallback(<K extends keyof T>(key: K, value: T[K]) => {
    setValues((current) => ({ ...current, [key]: value }));
  }, []);
  const reset = useCallback((next: T = initial) => setValues(next), [initial]);
  return { values, setValues, setField, reset };
}
