import { Link } from "react-router-dom";
import { ArrowUpRight, type LucideIcon } from "lucide-react";
import { formatNumber } from "../../utils";

interface Props {
  icon: LucideIcon;
  title: string;
  description: string;
  to: string;
  actionLabel: string;
  count?: number;
  countLabel?: string;
}

export function LinkedPanel({
  icon: Icon,
  title,
  description,
  to,
  actionLabel,
  count,
  countLabel,
}: Props) {
  return (
    <div className="card flex flex-col items-center gap-3 px-6 py-10 text-center sm:py-12">
      <span className="grid size-12 place-items-center rounded-full bg-app text-navy-800">
        <Icon size={22} />
      </span>
      <div>
        <h2 className="font-display text-base font-bold text-ink">{title}</h2>
        <p className="mx-auto mt-1 max-w-md text-xs leading-relaxed text-muted">{description}</p>
        {count !== undefined && count > 0 && (
          <p className="mt-2 inline-flex rounded-full bg-gold-300/40 px-3 py-1 text-[11px] font-semibold text-navy-900">
            {formatNumber(count)} {countLabel}
          </p>
        )}
      </div>
      <Link
        to={to}
        className="inline-flex items-center gap-1 rounded-lg border border-line px-3.5 py-2 text-xs font-semibold text-navy-800 transition hover:bg-app"
      >
        {actionLabel}
        <ArrowUpRight size={14} />
      </Link>
    </div>
  );
}
