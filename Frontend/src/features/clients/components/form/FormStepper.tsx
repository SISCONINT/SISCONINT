import clsx from "clsx";
import { Check } from "lucide-react";

export interface StepMeta {
  title: string;
  subtitle: string;
}

interface Props {
  steps: StepMeta[];
  current: number;
  maxVisited: number;
  onSelect: (index: number) => void;
}

export function FormStepper({ steps, current, maxVisited, onSelect }: Props) {
  return (
    <nav aria-label="Pasos del registro" className="card p-2.5">
      <ol className="grid grid-cols-2 gap-2 sm:grid-cols-3 lg:grid-cols-5">
        {steps.map((step, index) => {
          const completed = index < current;
          const active = index === current;
          const reachable = index <= maxVisited;

          return (
            <li key={step.title}>
              <button
                type="button"
                onClick={() => reachable && onSelect(index)}
                disabled={!reachable}
                aria-current={active ? "step" : undefined}
                className={clsx(
                  "flex h-full w-full items-center gap-2.5 rounded-lg px-2.5 py-2 text-left transition",
                  active && "bg-navy-900 text-white shadow-[0_6px_14px_rgb(11_20_69/18%)]",
                  !active && "bg-app/70 text-ink hover:bg-app",
                  !reachable && "cursor-not-allowed opacity-60",
                )}
              >
                <span
                  className={clsx(
                    "grid size-8 shrink-0 place-items-center rounded-full text-xs font-bold",
                    completed && "bg-gold-300 text-navy-900",
                    active && "bg-gold-300 text-navy-900",
                    !completed && !active && "bg-surface text-muted ring-1 ring-line",
                  )}
                >
                  {completed ? <Check size={15} strokeWidth={3} /> : index + 1}
                </span>
                <span className="min-w-0">
                  <span className="block truncate text-[11px] font-semibold uppercase tracking-wide">
                    Paso 0{index + 1}
                  </span>
                  <span className="block truncate text-[12px] font-semibold">
                    {step.title}
                  </span>
                  <span
                    className={clsx(
                      "block truncate text-[10px]",
                      active ? "text-on-dark" : completed ? "text-emerald-700" : "text-muted",
                    )}
                  >
                    {completed ? "Completado" : active ? "En captura" : step.subtitle}
                  </span>
                </span>
              </button>
            </li>
          );
        })}
      </ol>
    </nav>
  );
}
