import clsx from "clsx";
import { PERIODOS, PERIODO_LABELS, type Periodo } from "../types";

export function PeriodTabs({ value, onChange }: { value: Periodo; onChange: (p: Periodo) => void }) {
  return (
    <div className="flex flex-wrap gap-1.5 rounded-lg bg-field p-1">
      {PERIODOS.map((p) => (
        <button
          key={p}
          type="button"
          onClick={() => onChange(p)}
          className={clsx(
            "rounded-md px-3 py-1.5 text-[13px] font-medium transition-colors",
            value === p ? "bg-surface text-ink shadow-card" : "text-muted hover:text-ink",
          )}
        >
          {PERIODO_LABELS[p]}
        </button>
      ))}
    </div>
  );
}
