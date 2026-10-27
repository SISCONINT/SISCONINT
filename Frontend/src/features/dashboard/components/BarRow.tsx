interface Props {
  title: string;
  subtitle?: string;
  value: string;
  percent: number;
}

export function BarRow({ title, subtitle, value, percent }: Props) {
  return (
    <div>
      <div className="mb-1 flex items-baseline justify-between gap-2">
        <div className="min-w-0">
          <p className="truncate text-sm font-semibold text-ink">{title}</p>
          {subtitle && <p className="truncate text-[12px] text-muted">{subtitle}</p>}
        </div>
        <span className="shrink-0 text-sm font-semibold text-ink">{value}</span>
      </div>
      <div className="h-1.5 w-full overflow-hidden rounded-full bg-field">
        <div className="h-full bg-navy-700" style={{ width: `${Math.min(percent, 100)}%` }} />
      </div>
    </div>
  );
}
