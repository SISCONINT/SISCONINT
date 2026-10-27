import { Archive, CheckCircle2, PauseCircle, Users, type LucideIcon } from "lucide-react";
import clsx from "clsx";
import { formatNumber } from "../utils";

interface Props {
  activos: number;
  pausados: number;
  bajas: number;
  loading: boolean;
}

interface CardProps {
  label: string;
  value: number;
  hint: string;
  icon: LucideIcon;
  iconClass: string;
  barClass: string;
  percent: number;
  loading: boolean;
}

function KpiCard({ label, value, hint, icon: Icon, iconClass, barClass, percent, loading }: CardProps) {
  return (
    <article className="card p-4">
      <div className="flex items-start justify-between gap-3">
        <p className="text-[10px] font-semibold uppercase tracking-[0.12em] text-muted">{label}</p>
        <span className={clsx("grid size-8 shrink-0 place-items-center rounded-lg", iconClass)}>
          <Icon size={16} />
        </span>
      </div>

      {loading ? (
        <div className="mt-2 space-y-2" aria-hidden="true">
          <div className="h-8 w-16 animate-pulse rounded bg-line" />
          <div className="h-2 w-full animate-pulse rounded bg-line" />
        </div>
      ) : (
        <>
          <p className="mt-1 font-display text-3xl font-bold leading-none text-ink">
            {formatNumber(value)}
          </p>
          <p className="mt-2 text-[11px] text-muted">{hint}</p>
          <div className="mt-3 h-1.5 overflow-hidden rounded-full bg-line">
            <div
              className={clsx("h-full rounded-full", barClass)}
              style={{ width: `${Math.min(100, Math.max(0, percent))}%` }}
            />
          </div>
        </>
      )}
    </article>
  );
}

export function ClientsKpiCards({ activos, pausados, bajas, loading }: Props) {
  const total = activos + pausados + bajas;
  const percent = (value: number) => (total > 0 ? (value / total) * 100 : 0);

  return (
    <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
      <KpiCard
        label="Cartera total registrada"
        value={total}
        hint="Contribuyentes en el padrón"
        icon={Users}
        iconClass="bg-navy-900 text-gold-500"
        barClass="bg-navy-900"
        percent={total > 0 ? 100 : 0}
        loading={loading}
      />
      <KpiCard
        label="Operatividad regular"
        value={activos}
        hint={
          total > 0
            ? `${Math.round(percent(activos))}% de la cartera en atención`
            : "Sin contribuyentes registrados"
        }
        icon={CheckCircle2}
        iconClass="bg-gold-300/60 text-navy-900"
        barClass="bg-emerald-500"
        percent={percent(activos)}
        loading={loading}
      />
      <KpiCard
        label="Revisión o suspensión"
        value={pausados}
        hint="Pausados por revisión fiscal"
        icon={PauseCircle}
        iconClass="bg-app text-navy-800"
        barClass="bg-amber-400"
        percent={percent(pausados)}
        loading={loading}
      />
      <KpiCard
        label="Conclusión fiduciaria"
        value={bajas}
        hint="Bajas y liquidaciones concluidas"
        icon={Archive}
        iconClass="bg-app text-muted"
        barClass="bg-slate-300"
        percent={percent(bajas)}
        loading={loading}
      />
    </div>
  );
}
