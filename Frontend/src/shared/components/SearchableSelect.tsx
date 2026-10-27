import { useEffect, useRef, useState } from "react";
import { ChevronDown, Search, X } from "lucide-react";
import clsx from "clsx";

export interface SelectOption {
  value: number;
  label: string;
  sublabel?: string;
}

interface Props {
  value: number | null;
  onChange: (value: number | null) => void;
  options: SelectOption[];
  query: string;
  onQueryChange: (q: string) => void;
  loading?: boolean;
  placeholder?: string;
  invalid?: boolean;
  disabled?: boolean;
}

/** Select con búsqueda remota: usado donde el listado real pagina a 20 registros (RG-07). */
export function SearchableSelect({
  value,
  onChange,
  options,
  query,
  onQueryChange,
  loading,
  placeholder = "Buscar…",
  invalid,
  disabled,
}: Props) {
  const [open, setOpen] = useState(false);
  const rootRef = useRef<HTMLDivElement>(null);
  const selected = options.find((o) => o.value === value);

  useEffect(() => {
    function onClickOutside(e: MouseEvent) {
      if (rootRef.current && !rootRef.current.contains(e.target as Node)) setOpen(false);
    }
    document.addEventListener("mousedown", onClickOutside);
    return () => document.removeEventListener("mousedown", onClickOutside);
  }, []);

  return (
    <div ref={rootRef} className="relative">
      <button
        type="button"
        disabled={disabled}
        onClick={() => setOpen((o) => !o)}
        aria-invalid={invalid}
        className={clsx(
          "flex w-full items-center justify-between gap-2 rounded-lg bg-field py-3 pl-4 pr-3 text-left text-sm text-ink outline-none ring-1 ring-transparent transition focus:ring-gold-500 aria-[invalid=true]:ring-danger disabled:opacity-60",
        )}
      >
        <span className={selected ? "truncate text-ink" : "truncate text-muted/70"}>
          {selected ? selected.label : placeholder}
        </span>
        <ChevronDown size={16} className="shrink-0 text-muted" />
      </button>

      {open && !disabled && (
        <div className="absolute z-20 mt-1.5 w-full overflow-hidden rounded-lg border border-line bg-surface shadow-[0_12px_30px_rgb(16_24_40/15%)]">
          <div className="flex items-center gap-2 border-b border-line px-3 py-2">
            <Search size={14} className="shrink-0 text-muted" />
            <input
              autoFocus
              value={query}
              onChange={(e) => onQueryChange(e.target.value)}
              placeholder="Escribe para buscar…"
              className="w-full bg-transparent text-sm text-ink outline-none"
            />
            {selected && (
              <button
                type="button"
                onClick={() => {
                  onChange(null);
                  setOpen(false);
                }}
                className="shrink-0 text-muted hover:text-ink"
                aria-label="Quitar selección"
              >
                <X size={14} />
              </button>
            )}
          </div>
          <ul className="max-h-56 overflow-y-auto">
            {loading ? (
              <li className="px-3 py-2.5 text-sm text-muted">Buscando…</li>
            ) : options.length === 0 ? (
              <li className="px-3 py-2.5 text-sm text-muted">Sin resultados</li>
            ) : (
              options.map((o) => (
                <li key={o.value}>
                  <button
                    type="button"
                    onClick={() => {
                      onChange(o.value);
                      setOpen(false);
                    }}
                    className={clsx(
                      "flex w-full flex-col items-start px-3 py-2 text-left text-sm hover:bg-field",
                      o.value === value && "bg-gold-300/30",
                    )}
                  >
                    <span className="text-ink">{o.label}</span>
                    {o.sublabel && <span className="text-[12px] text-muted">{o.sublabel}</span>}
                  </button>
                </li>
              ))
            )}
          </ul>
        </div>
      )}
    </div>
  );
}
