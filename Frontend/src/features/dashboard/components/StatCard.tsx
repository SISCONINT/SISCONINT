import type { LucideIcon } from "lucide-react";
import clsx from "clsx";
import type { ReactNode } from "react";

interface Props {
  icon: LucideIcon;
  label: string;
  value: ReactNode;
  hint?: ReactNode;
  tone?: "default" | "danger" | "gold";
}

export function StatCard({ icon: Icon, label, value, hint, tone = "default" }: Props) {
  return (
    <div className="card p-4">
      <div className="mb-2 flex items-center justify-between">
        <p className="text-[11px] font-semibold uppercase tracking-wide text-muted">{label}</p>
        <span
          className={clsx(
            "grid size-7 place-items-center rounded-lg",
            tone === "danger" ? "bg-red-50 text-danger" : tone === "gold" ? "bg-gold-300/40 text-gold-700" : "bg-field text-muted",
          )}
        >
          <Icon size={15} />
        </span>
      </div>
      <p className={clsx("font-display text-2xl font-bold", tone === "danger" ? "text-danger" : "text-ink")}>{value}</p>
      {hint && <div className="mt-1 text-[12px] text-muted">{hint}</div>}
    </div>
  );
}
