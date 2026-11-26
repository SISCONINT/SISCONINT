import { useState } from "react";
import { BarChart3, Download, Printer } from "lucide-react";
import { BTN_SECONDARY } from "@/shared/components/buttons";
import { useDashboardGerencial } from "@/features/dashboard/api/useDashboardGerencial";
import { PeriodTabs } from "@/features/dashboard/components/PeriodTabs";
import { BarRow } from "@/features/dashboard/components/BarRow";
import type { Periodo } from "@/features/dashboard/types";
import { downloadCsv } from "../utils/csv";

export function ReportsPage() {
  const [periodo, setPeriodo] = useState<Periodo>("MES_ACTUAL");
  const { data, isLoading, isError } = useDashboardGerencial({ periodo });

  return (
    <div className="mx-auto flex w-full max-w-5xl flex-col gap-4">
      <header className="flex flex-wrap items-start justify-between gap-3 print:hidden">
        <div>
          <nav aria-label="Ruta de navegación" className="mb-1 flex items-center gap-1.5 text-[11px] text-muted">
            <span>Control y análisis</span>
            <span aria-hidden="true">/</span>
            <span className="font-semibold text-navy-800">Reportes ejecutivos</span>
          </nav>
          <div className="flex items-center gap-2">
            <BarChart3 size={20} className="text-gold-700" />
            <h1 className="font-display text-2xl font-bold text-ink">Reportes ejecutivos</h1>
          </div>
          <p className="mt-1.5 text-sm text-muted">Resumen de horas, clientes y tareas del periodo, listo para imprimir o exportar.</p>
        </div>
        <div className="flex items-center gap-2">
          <button type="button" onClick={() => window.print()} className={BTN_SECONDARY}>
            <Printer size={15} /> Imprimir / PDF
          </button>
        </div>
      </header>

      <div className="print:hidden">
        <PeriodTabs value={periodo} onChange={setPeriodo} />
      </div>

      {isLoading ? (
        <p className="text-sm text-muted">Generando reporte…</p>
      ) : isError || !data ? (
        <p className="text-sm text-danger">No se pudo generar el reporte.</p>
      ) : (
        <>
          <div className="card p-5 print:border-0 print:shadow-none">
            <p className="text-[11px] font-semibold uppercase tracking-wide text-muted">{data.periodo.etiqueta}</p>
            <p className="font-display text-xl font-bold text-ink">
              {data.tarjetas.horas_totales.horas.toFixed(1)} hrs trabajadas · {data.tarjetas.tareas_activas} tareas activas ·{" "}
              {data.tarjetas.tareas_vencidas} vencidas
            </p>
            {data.tarjetas.costo_estimado?.disponible && (
              <p className="mt-1 text-sm text-muted">Costo estimado: ${(data.tarjetas.costo_estimado.monto ?? 0).toLocaleString("es-MX")}</p>
            )}
          </div>

          <div className="card p-5">
            <div className="mb-3 flex items-center justify-between">
              <h2 className="font-semibold text-ink">Horas por colaborador</h2>
              <button
                type="button"
                onClick={() =>
                  downloadCsv("horas-por-colaborador.csv", [
                    ["Colaborador", "Horas"],
                    ...data.tiempo_por_empleado.map((e) => [e.nombre, e.horas.toFixed(1)]),
                  ])
                }
                className="flex items-center gap-1.5 text-[13px] font-medium text-navy-700 hover:underline print:hidden"
              >
                <Download size={13} /> CSV
              </button>
            </div>
            <div className="flex flex-col gap-3">
              {data.tiempo_por_empleado.map((e) => (
                <BarRow key={e.colaborador_id} title={e.nombre} value={`${e.horas.toFixed(1)} hrs`} percent={(e.horas / (data.tiempo_por_empleado[0]?.horas || 1)) * 100} />
              ))}
            </div>
          </div>

          <div className="card p-5">
            <div className="mb-3 flex items-center justify-between">
              <h2 className="font-semibold text-ink">Horas por cliente</h2>
              <button
                type="button"
                onClick={() =>
                  downloadCsv("horas-por-cliente.csv", [
                    ["Cliente", "Horas"],
                    ...data.tiempo_por_cliente.map((c) => [c.nombre, c.horas.toFixed(1)]),
                  ])
                }
                className="flex items-center gap-1.5 text-[13px] font-medium text-navy-700 hover:underline print:hidden"
              >
                <Download size={13} /> CSV
              </button>
            </div>
            <div className="flex flex-col gap-3">
              {data.tiempo_por_cliente.map((c) => (
                <BarRow key={c.cliente_id} title={c.nombre} value={`${c.horas.toFixed(1)} hrs`} percent={(c.horas / (data.tiempo_por_cliente[0]?.horas || 1)) * 100} />
              ))}
            </div>
          </div>

          <div className="card p-5">
            <h2 className="mb-3 font-semibold text-ink">Estado de tareas</h2>
            <div className="grid grid-cols-2 gap-3 sm:grid-cols-5">
              {(["POR_HACER", "EN_PROGRESO", "EN_REVISION", "COMPLETADO", "vencidas"] as const).map((k) => (
                <div key={k} className="rounded-lg bg-field/70 px-3 py-2.5 text-center">
                  <p className="text-[11px] uppercase text-muted">{k.replace("_", " ")}</p>
                  <p className="text-lg font-bold text-ink">{data.estado_tareas[k]}</p>
                </div>
              ))}
            </div>
          </div>
        </>
      )}
    </div>
  );
}
