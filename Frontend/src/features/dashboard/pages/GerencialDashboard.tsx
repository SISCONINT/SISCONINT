import { useState } from "react";
import { Link } from "react-router-dom";
import { AlertTriangle, Banknote, Clock, ListChecks, Plus, TrendingDown, TrendingUp } from "lucide-react";
import { StatCard } from "../components/StatCard";
import { BarRow } from "../components/BarRow";
import { DonutChart } from "../components/DonutChart";
import { PeriodTabs } from "../components/PeriodTabs";
import { useDashboardGerencial } from "../api/useDashboardGerencial";
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

export function GerencialDashboard() {
  const [periodo, setPeriodo] = useState<Periodo>("MES_ACTUAL");
  const filters: DashboardFilters = { periodo };
  const { data, isLoading, isError } = useDashboardGerencial(filters);

  return (
    <div>
      <div className="mb-5 flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="font-display text-xl font-bold text-ink sm:text-2xl">Dashboard Gerencial y Control Operativo</h1>
          <p className="mt-0.5 text-sm text-muted">Consolidado de productividad, horas y tareas del despacho.</p>
        </div>
        <Link to="/tareas" className="flex items-center gap-2 rounded-lg bg-gold-300 px-4 py-2.5 text-sm font-semibold text-ink hover:brightness-95">
          <Plus size={16} /> Nueva tarea
        </Link>
      </div>

      <div className="mb-5">
        <PeriodTabs value={periodo} onChange={setPeriodo} />
      </div>

      {isLoading ? (
        <p className="text-sm text-muted">Cargando dashboard…</p>
      ) : isError || !data ? (
        <p className="text-sm text-danger">No se pudo cargar el dashboard.</p>
      ) : data.sin_informacion ? (
        <p className="card p-6 text-sm text-muted">{data.mensaje ?? "Sin información para este periodo."}</p>
      ) : (
        <>
          <div className="mb-5 grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-4">
            <StatCard
              icon={Clock}
              label={`Horas totales (${data.periodo.etiqueta})`}
              value={`${data.tarjetas.horas_totales.horas.toFixed(1)} hrs`}
              hint={
                data.tarjetas.horas_totales.variacion_porcentaje !== null && (
                  <span className="flex items-center gap-1">
                    {data.tarjetas.horas_totales.variacion_porcentaje >= 0 ? (
                      <TrendingUp size={13} className="text-emerald-600" />
                    ) : (
                      <TrendingDown size={13} className="text-danger" />
                    )}
                    {data.tarjetas.horas_totales.variacion_porcentaje.toFixed(1)}% vs periodo anterior (
                    {data.tarjetas.horas_totales.horas_periodo_anterior.toFixed(1)} hrs)
                  </span>
                )
              }
            />
            <StatCard icon={ListChecks} label="Tareas activas" value={data.tarjetas.tareas_activas} />
            <StatCard
              icon={AlertTriangle}
              label="Tareas vencidas"
              value={data.tarjetas.tareas_vencidas}
              tone={data.tarjetas.tareas_vencidas > 0 ? "danger" : "default"}
            />
            <StatCard
              icon={Banknote}
              label="Costo estimado"
              value={
                data.tarjetas.costo_estimado?.disponible
                  ? `$${(data.tarjetas.costo_estimado.monto ?? 0).toLocaleString("es-MX")}`
                  : "No disponible"
              }
              hint={data.tarjetas.costo_estimado?.mensaje}
            />
          </div>

          <div className="mb-5 grid grid-cols-1 gap-5 lg:grid-cols-2">
            <div className="card p-5">
              <h2 className="mb-3 font-semibold text-ink">Horas por colaborador</h2>
              {data.tiempo_por_empleado.length === 0 ? (
                <p className="text-sm text-muted">Sin registros en este periodo.</p>
              ) : (
                <div className="flex flex-col gap-3.5">
                  {data.tiempo_por_empleado.slice(0, 8).map((e) => (
                    <BarRow
                      key={e.colaborador_id}
                      title={e.nombre}
                      value={`${e.horas.toFixed(1)} hrs`}
                      percent={(e.horas / (data.tiempo_por_empleado[0]?.horas || 1)) * 100}
                    />
                  ))}
                </div>
              )}
            </div>

            <div className="card p-5">
              <h2 className="mb-3 font-semibold text-ink">Horas por cliente</h2>
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
          </div>

          <div className="grid grid-cols-1 gap-5 lg:grid-cols-2">
            <div className="card p-5">
              <h2 className="mb-3 font-semibold text-ink">Distribución por categoría</h2>
              <DonutChart
                slices={data.distribucion_por_categoria.map((c) => ({ nombre: c.nombre, porcentaje: c.porcentaje, color: "" }))}
                centerValue={data.tarjetas.horas_totales.horas.toFixed(1)}
                centerLabel="HRS TOTAL"
              />
            </div>

            <div className="card p-5">
              <h2 className="mb-1 font-semibold text-ink">Estado de tareas</h2>
              <p className="mb-3 text-[12px] text-muted">{data.estado_tareas.total} tareas totales</p>
              <div className="mb-4 flex h-2.5 w-full overflow-hidden rounded-full bg-field">
                {(["POR_HACER", "EN_PROGRESO", "EN_REVISION", "COMPLETADO"] as const).map((k) => (
                  <div
                    key={k}
                    className={COLUMN_TONE[k]}
                    style={{ width: data.estado_tareas.total ? `${(data.estado_tareas[k] / data.estado_tareas.total) * 100}%` : 0 }}
                  />
                ))}
              </div>
              <div className="grid grid-cols-2 gap-3">
                {(["POR_HACER", "EN_PROGRESO", "EN_REVISION", "COMPLETADO"] as const).map((k) => (
                  <div key={k} className="rounded-lg bg-field/70 px-3 py-2.5">
                    <p className="flex items-center gap-1.5 text-[12px] text-muted">
                      <span className={`size-2 rounded-full ${COLUMN_TONE[k]}`} /> {COLUMN_LABEL[k]}
                    </p>
                    <p className="text-lg font-bold text-ink">{data.estado_tareas[k]}</p>
                  </div>
                ))}
              </div>
              {data.estado_tareas.vencidas > 0 && (
                <p className="mt-3 text-[13px] font-medium text-danger">{data.estado_tareas.vencidas} tareas vencidas requieren atención.</p>
              )}
              <Link to="/tablero" className="mt-4 inline-block text-[13px] font-medium text-navy-700 hover:underline">
                Ver tablero completo →
              </Link>
            </div>
          </div>
        </>
      )}
    </div>
  );
}
