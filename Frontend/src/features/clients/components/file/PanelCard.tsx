import type { ReactNode } from "react";
import type { LucideIcon } from "lucide-react";
import clsx from "clsx";

interface Props {
  icon: LucideIcon;
  title: string;
  subtitle?: string;
  aside?: ReactNode;
  className?: string;
  children: ReactNode;
}

export function PanelCard({ icon: Icon, title, subtitle, aside, className, children }: Props) {
  return (
    <section className={clsx("card p-4", className)}>
      <header className="mb-3 flex items-start justify-between gap-2">
        <div className="flex items-start gap-2">
          <span className="mt-0.5 grid size-7 shrink-0 place-items-center rounded-md bg-app text-navy-800">
            <Icon size={15} />
          </span>
          <div>
            <h2 className="text-[13px] font-semibold text-ink">{title}</h2>
            {subtitle && <p className="text-[10.5px] text-muted">{subtitle}</p>}
          </div>
        </div>
        {aside}
      </header>
      {children}
    </section>
  );
}
