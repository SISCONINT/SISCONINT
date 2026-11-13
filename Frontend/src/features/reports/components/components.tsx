import type { ReactNode } from "react";
import {
  AlertTriangle,
  BarChart3,
  CheckCircle2,
  Clock3,
  DollarSign,
  ListChecks,
  Users,
} from "lucide-react";
import { StatCard } from "@/shared/components/components";
import { formatHours, formatMoney } from "@/shared/utils/utils";
import type { ReportData, ReportEstadoTareas } from "../types";

export function ReportKpis({ data }: { data: ReportData }) {
  const { tarjetas, tareas_completadas } = data;
  const costo = tarjetas.costo_estimado;

  return (
    <section className="grid gap-3 sm:grid-cols-2 xl:grid-cols-5">
      <StatCard
        label="Horas registradas"
        value={`${tarjetas.horas_totales.horas} h`}
        hint={
          tarjetas.horas_totales.variacion_porcentaje === null
            ? "Sin periodo anterior comparable"
            : `${tarjetas.horas_totales.variacion_porcentaje}% vs. periodo anterior`
        }
        icon={<Clock3 size={18} />}
      />
      <StatCard
        label="Tareas activas"
        value={tarjetas.tareas_activas}
        hint="Sin contar completadas"
        icon={<ListChecks size={18} />}
      />
      <StatCard
        label="Tareas vencidas"
        value={tarjetas.tareas_vencidas}
        hint="Requieren atención"
        icon={<AlertTriangle size={18} />}
        tone={tarjetas.tareas_vencidas > 0 ? "danger" : "success"}
      />
      <StatCard
        label="Tareas completadas"
        value={tareas_completadas}
        hint="Cerradas dentro del periodo"
        icon={<CheckCircle2 size={18} />}
        tone="success"
      />
      {costo && (
        <StatCard
          label="Costo estimado"
          value={costo.disponible ? formatMoney(costo.monto) : "No disponible"}
          hint={costo.mensaje || "Horas × tarifa configurada"}
          icon={<DollarSign size={18} />}
          tone={costo.disponible ? "default" : "warning"}
        />
      )}
    </section>
  );
}

interface BreakdownRow {
  id: number;
  label: string;
  minutos: number;
  extra?: string;
}

export function ReportBreakdown({
  title,
  icon,
  rows,
  empty,
}: {
  title: string;
  icon: ReactNode;
  rows: BreakdownRow[];
  empty: string;
}) {
  const max = Math.max(1, ...rows.map((row) => row.minutos));

  return (
    <section className="card p-4">
      <header className="flex items-center gap-2">
        <span className="grid size-8 place-items-center rounded-lg bg-app text-navy-800">{icon}</span>
        <h2 className="text-sm font-semibold text-ink">{title}</h2>
      </header>
      {rows.length === 0 ? (
        <p className="mt-6 text-center text-xs text-muted">{empty}</p>
      ) : (
        <ul className="mt-4 flex flex-col gap-3">
          {rows.map((row) => (
            <li key={row.id}>
              <div className="flex items-center justify-between gap-3 text-xs">
                <span className="truncate font-medium text-ink">{row.label}</span>
                <span className="shrink-0 text-muted">
                  {formatHours(row.minutos)}
                  {row.extra ? ` · ${row.extra}` : ""}
                </span>
              </div>
              <div className="mt-1 h-2 overflow-hidden rounded-full bg-app">
                <div
                  className="h-full rounded-full bg-gradient-to-r from-navy-800 to-gold-500"
                  style={{ width: `${Math.max(4, (row.minutos / max) * 100)}%` }}
                />
              </div>
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}

export function ReportTeamBreakdown({ data }: { data: ReportData }) {
  return (
    <ReportBreakdown
      title="Horas por colaborador"
      icon={<Users size={17} />}
      rows={(data.tiempo_por_empleado ?? []).map((row) => ({
        id: row.colaborador_id,
        label: row.nombre,
        minutos: row.minutos,
      }))}
      empty="Sin horas registradas en el periodo."
    />
  );
}

export function ReportClientBreakdown({ data }: { data: ReportData }) {
  return (
    <ReportBreakdown
      title="Horas por cliente"
      icon={<BarChart3 size={17} />}
      rows={(data.tiempo_por_cliente ?? []).map((row) => ({
        id: row.cliente_id,
        label: row.nombre,
        minutos: row.minutos,
      }))}
      empty="Sin horas registradas en el periodo."
    />
  );
}

export function ReportCategoryBreakdown({ data }: { data: ReportData }) {
  return (
    <ReportBreakdown
      title="Distribución por categoría"
      icon={<BarChart3 size={17} />}
      rows={(data.distribucion_por_categoria ?? []).map((row) => ({
        id: row.categoria_id,
        label: row.nombre,
        minutos: row.minutos,
        extra: `${row.porcentaje}%`,
      }))}
      empty="Sin horas clasificadas en el periodo."
    />
  );
}

export function ReportTaskStatus({ estado }: { estado: ReportEstadoTareas }) {
  const rows = [
    { key: "POR_HACER", label: "Por hacer", value: estado.POR_HACER ?? 0, color: "bg-slate-400" },
    { key: "EN_PROGRESO", label: "En progreso", value: estado.EN_PROGRESO ?? 0, color: "bg-sky-500" },
    { key: "EN_REVISION", label: "En revisión", value: estado.EN_REVISION ?? 0, color: "bg-amber-500" },
    { key: "COMPLETADO", label: "Completado", value: estado.COMPLETADO ?? 0, color: "bg-emerald-500" },
  ];

  return (
    <section className="card p-4">
      <header className="flex items-center gap-2">
        <span className="grid size-8 place-items-center rounded-lg bg-app text-navy-800">
          <CheckCircle2 size={17} />
        </span>
        <h2 className="text-sm font-semibold text-ink">Estado de las tareas</h2>
        <span className="ml-auto text-xs text-muted">{estado.total ?? 0} tareas</span>
      </header>
      <div className="mt-4 grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
        {rows.map((row) => (
          <div key={row.key} className="rounded-xl border border-line bg-app/40 p-3">
            <div className="flex items-center gap-2">
              <span className={`size-2 rounded-full ${row.color}`} />
              <span className="text-xs font-medium text-muted">{row.label}</span>
            </div>
            <p className="mt-1 font-display text-xl font-bold text-ink">{row.value}</p>
          </div>
        ))}
      </div>
      {(estado.vencidas ?? 0) > 0 && (
        <p className="mt-3 text-xs font-medium text-danger">
          {estado.vencidas} tareas vencidas sin completar.
        </p>
      )}
    </section>
  );
}
