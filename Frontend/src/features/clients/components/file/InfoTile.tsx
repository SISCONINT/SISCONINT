import type { ReactNode } from "react";
import clsx from "clsx";

interface Props {
  label: string;
  value?: ReactNode;
  hint?: string;
  className?: string;
}

export function InfoTile({ label, value, hint, className }: Props) {
  const empty = value === null || value === undefined || value === "";

  return (
    <div className={clsx("rounded-lg bg-app/70 px-3 py-2.5", className)}>
      <p className="text-[9px] font-semibold uppercase tracking-[0.12em] text-muted">{label}</p>
      <div className="mt-0.5 text-[12.5px] font-semibold leading-snug text-ink">
        {empty ? <span className="font-normal italic text-muted">No registrado</span> : value}
      </div>
      {hint && <p className="mt-0.5 text-[10px] leading-snug text-muted">{hint}</p>}
    </div>
  );
}
