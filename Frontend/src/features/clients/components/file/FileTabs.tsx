import clsx from "clsx";
import type { LucideIcon } from "lucide-react";

export type FileTabId =
  | "general"
  | "fiscal"
  | "contactos"
  | "obligaciones"
  | "tareas"
  | "minutas";

export interface FileTab {
  id: FileTabId;
  label: string;
  icon: LucideIcon;
  badge?: number;
}

interface Props {
  tabs: FileTab[];
  active: FileTabId;
  onChange: (tab: FileTabId) => void;
}

export function FileTabs({ tabs, active, onChange }: Props) {
  return (
    <nav aria-label="Secciones del expediente" className="card p-1.5">
      <div role="tablist" className="flex flex-wrap gap-1">
        {tabs.map(({ id, label, icon: Icon, badge }) => {
          const selected = id === active;
          return (
            <button
              key={id}
              type="button"
              role="tab"
              aria-selected={selected}
              onClick={() => onChange(id)}
              className={clsx(
                "inline-flex shrink-0 items-center gap-1.5 rounded-md px-3 py-2 text-[11.5px] font-semibold transition",
                selected
                  ? "bg-navy-900 text-white shadow-[0_4px_10px_rgb(11_20_69/16%)]"
                  : "text-muted hover:bg-app hover:text-navy-800",
              )}
            >
              <Icon size={14} />
              {label}
              {badge !== undefined && badge > 0 && (
                <span
                  className={clsx(
                    "rounded-full px-1.5 py-0.5 text-[9px] font-bold",
                    selected ? "bg-gold-300 text-navy-900" : "bg-gold-300/50 text-navy-900",
                  )}
                >
                  {badge}
                </span>
              )}
            </button>
          );
        })}
      </div>
    </nav>
  );
}
