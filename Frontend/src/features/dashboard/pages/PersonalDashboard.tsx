import { useState } from "react";
import { Link } from "react-router-dom";
import { AlertTriangle, Clock, ListChecks, Plus, TrendingDown, TrendingUp } from "lucide-react";
import { StatCard } from "../components/StatCard";
import { BarRow } from "../components/BarRow";
import { DonutChart } from "../components/DonutChart";
import { PeriodTabs } from "../components/PeriodTabs";
import { useDashboardPersonal } from "../api/useDashboardPersonal";
import type { DashboardFilters, Periodo } from "../types";

const COLUMN_TONE: Record<string, string> = {
  POR_HACER: "bg-muted",
  EN_PROGRESO: "bg-navy-700",
  EN_REVISION: "bg-amber-500",
  COMPLETADO: "bg-emerald-500",
};

const COLUMN_LABEL: Record<string, string> = {
  POR_HACER: "Por hacer",
  EN_PROGRESO: "En progreso",
  EN_REVISION: "En revisión",
  COMPLETADO: "Completado",
};

export function PersonalDashboard() {
  const [periodo, setPeriodo] = useState<Periodo>("MES_ACTUAL");
  const filters: DashboardFilters = { periodo };
  const { data, isLoading, isError } = useDashboardPersonal(filters);

  return (
    <div>
      <div className="mb-5 flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="font-display text-xl font-bold text-ink sm:text-2xl">Mi Panel Operativo y Desempeño</h1>
          <p className="mt-0.5 text-sm text-muted">Seguimiento de tus tareas y horas registradas.</p>
        </div>
        <Link to="/tareas" className="flex items-center gap-2 rounded-lg bg-gold-300 px-4 py-2.5 text-sm font-semibold text-ink hover:brightness-95">
          <Plus size={16} /> Nueva tarea
        </Link>
      </div>

      <div className="mb-5">
        <PeriodTabs value={periodo} onChange={setPeriodo} />
      </div>

      {isLoading ? (
        <p className="text-sm text-muted">Cargando tu panel…</p>
      ) : isError || !data ? (
        <p className="text-sm text-danger">No se pudo cargar tu panel.</p>
      ) : data.sin_informacion ? (
        <p className="card p-6 text-sm text-muted">{data.mensaje ?? "Sin información para este periodo."}</p>
      ) : (
        <>
          <div className="mb-5 grid grid-cols-1 gap-3 sm:grid-cols-3">
            <StatCard
              icon={Clock}
              label={`Mis horas (${data.periodo.etiqueta})`}
              value={`${data.tarjetas.horas_totales.horas.toFixed(1)} hrs`}
              hint={
                data.tarjetas.horas_totales.variacion_porcentaje !== null && (
                  <span className="flex items-center gap-1">
                    {data.tarjetas.horas_totales.variacion_porcentaje >= 0 ? (
                      <TrendingUp size={13} className="text-emerald-600" />
                    ) : (
                      <TrendingDown size={13} className="text-danger" />
                    )}
                    {data.tarjetas.horas_totales.variacion_porcentaje.toFixed(1)}% vs periodo anterior
                  </span>
                )
              }
            />
            <StatCard icon={ListChecks} label="Mis tareas activas" value={data.tarjetas.tareas_activas} />
            <StatCard
              icon={AlertTriangle}
              label="Mis tareas vencidas"
              value={data.tarjetas.tareas_vencidas}
              tone={data.tarjetas.tareas_vencidas > 0 ? "danger" : "default"}
            />
          </div>

          <div className="mb-5 grid grid-cols-1 gap-5 lg:grid-cols-2">
            <div className="card p-5">
              <h2 className="mb-3 font-semibold text-ink">Mis horas por cliente</h2>
              {data.tiempo_por_cliente.length === 0 ? (
                <p className="text-sm text-muted">Sin registros en este periodo.</p>
              ) : (
                <div className="flex flex-col gap-3.5">
                  {data.tiempo_por_cliente.slice(0, 8).map((c, i) => (
                    <BarRow
                      key={c.cliente_id}
                      title={`${i + 1}. ${c.nombre}`}
                      value={`${c.horas.toFixed(1)} hrs`}
                      percent={(c.horas / (data.tiempo_por_cliente[0]?.horas || 1)) * 100}
                    />
                  ))}
                </div>
              )}
            </div>

            <div className="card p-5">
              <h2 className="mb-3 font-semibold text-ink">Mis horas por categoría</h2>
              <DonutChart
                slices={data.distribucion_por_categoria.map((c) => ({ nombre: c.nombre, porcentaje: c.porcentaje, color: "" }))}
                centerValue={data.tarjetas.horas_totales.horas.toFixed(1)}
                centerLabel="HRS TOTALES"
              />
            </div>
          </div>

          <div className="card p-5">
            <h2 className="mb-1 font-semibold text-ink">Pipeline de mis tareas</h2>
            <p className="mb-3 text-[12px] text-muted">{data.estado_tareas.total} tareas asignadas</p>
            <div className="mb-4 flex h-2.5 w-full overflow-hidden rounded-full bg-field">
              {(["POR_HACER", "EN_PROGRESO", "EN_REVISION", "COMPLETADO"] as const).map((k) => (
                <div
                  key={k}
                  className={COLUMN_TONE[k]}
                  style={{ width: data.estado_tareas.total ? `${(data.estado_tareas[k] / data.estado_tareas.total) * 100}%` : 0 }}
                />
              ))}
            </div>
            <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
              {(["POR_HACER", "EN_PROGRESO", "EN_REVISION", "COMPLETADO"] as const).map((k) => (
                <div key={k} className="rounded-lg bg-field/70 px-3 py-2.5">
                  <p className="flex items-center gap-1.5 text-[12px] text-muted">
                    <span className={`size-2 rounded-full ${COLUMN_TONE[k]}`} /> {COLUMN_LABEL[k]}
                  </p>
                  <p className="text-lg font-bold text-ink">{data.estado_tareas[k]}</p>
                </div>
              ))}
            </div>
            <Link to="/tareas" className="mt-4 inline-block text-[13px] font-medium text-navy-700 hover:underline">
              Ver todas mis tareas →
            </Link>
          </div>
        </>
      )}
    </div>
  );
}
