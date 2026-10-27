import { Link } from "react-router-dom";
import { AlertTriangle, Banknote, Clock, ListChecks, Plus } from "lucide-react";
import { PageHeader } from "@/shared/components/PageHeader";
import { useAuthStore } from "@/shared/auth/authStore";
import { useTaskBoard } from "@/features/tasks/api/useTasks";
import { estadoLabel } from "@/shared/utils/format";
import { StatCard } from "../components/StatCard";
import { BarRow } from "../components/BarRow";
import { DonutChart } from "../components/DonutChart";
import { SampleBadge } from "../components/SampleBadge";
import { DISTRIBUCION_CATEGORIA, HORAS_POR_CLIENTE, HORAS_POR_EMPLEADO, COSTO_DEVENGADO } from "../mockData";

const COLUMN_TONE: Record<string, string> = {
  POR_HACER: "bg-muted",
  EN_PROGRESO: "bg-navy-700",
  EN_REVISION: "bg-amber-500",
  COMPLETADO: "bg-emerald-500",
};

export function GerencialDashboard() {
  const user = useAuthStore((s) => s.user);
  const { data: board, isLoading } = useTaskBoard({});

  const columnas = board?.columnas ?? [];
  const activas = columnas.filter((c) => c.estado !== "COMPLETADO").reduce((acc, c) => acc + c.total, 0);
  const vencidas = columnas
    .filter((c) => c.estado !== "COMPLETADO")
    .reduce((acc, c) => acc + c.tareas.filter((t) => t.semaforo === "ROJO").length, 0);
  const totalTareas = board?.total_tareas ?? 0;

  return (
    <div>
      <PageHeader
        title="Dashboard Gerencial y Control Operativo"
        subtitle={`Consolidado de productividad, horas facturables y tareas del despacho. Vista restringida: ${user ? user.nombre : ""}.`}
        actions={
          <Link to="/tareas/nuevo" className="flex items-center gap-2 rounded-lg bg-gold-300 px-4 py-2.5 text-sm font-semibold text-ink hover:brightness-95">
            <Plus size={16} /> Nueva tarea
          </Link>
        }
      />

      <div className="mb-5 grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-4">
        <StatCard icon={Clock} label="Horas totales trabajadas (ejemplo)" value="1,248.5 hrs" hint="+14.2% vs periodo anterior" />
        <StatCard
          icon={ListChecks}
          label="Tareas activas"
          value={isLoading ? "…" : activas}
          hint={columnas
            .filter((c) => c.estado !== "COMPLETADO")
            .map((c) => `${c.total} ${estadoLabel(c.estado)}`)
            .join(" · ")}
        />
        <StatCard
          icon={AlertTriangle}
          label="Vencimientos críticos"
          value={isLoading ? "…" : vencidas}
          tone={vencidas > 0 ? "danger" : "default"}
          hint="Tareas con semáforo rojo"
        />
        <StatCard icon={Banknote} label="Costo estimado y devengado (ejemplo)" value={`$${COSTO_DEVENGADO.monto.toLocaleString("es-MX")}`} hint={`Tarifa promedio: $${COSTO_DEVENGADO.tarifaPromedio} MXN/hr`} />
      </div>

      <div className="mb-5 grid grid-cols-1 gap-5 lg:grid-cols-2">
        <div className="card p-5">
          <div className="mb-3 flex items-center justify-between">
            <div>
              <h2 className="font-semibold text-ink">Horas por empleado</h2>
              <p className="text-[12px] text-muted">Rendimiento contra meta de 160 hrs mensuales</p>
            </div>
            <SampleBadge />
          </div>
          <div className="flex flex-col gap-3.5">
            {HORAS_POR_EMPLEADO.map((e) => (
              <BarRow key={e.nombre} title={e.nombre} subtitle={e.rol} value={`${e.horas.toFixed(1)} hrs (${e.porcentaje}%)`} percent={e.porcentaje} />
            ))}
          </div>
        </div>

        <div className="card p-5">
          <div className="mb-3 flex items-center justify-between">
            <div>
              <h2 className="font-semibold text-ink">Horas por cliente</h2>
              <p className="text-[12px] text-muted">Top 5 cuentas con mayor volumen</p>
            </div>
            <SampleBadge />
          </div>
          <div className="flex flex-col gap-3.5">
            {HORAS_POR_CLIENTE.map((c, i) => (
              <BarRow
                key={c.nombre}
                title={`${i + 1}. ${c.nombre}`}
                value={`${c.horas.toFixed(1)} hrs ($${c.monto.toLocaleString("es-MX")})`}
                percent={(c.horas / HORAS_POR_CLIENTE[0].horas) * 100}
              />
            ))}
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 gap-5 lg:grid-cols-2">
        <div className="card p-5">
          <div className="mb-3 flex items-center justify-between">
            <div>
              <h2 className="font-semibold text-ink">Distribución del tiempo por categoría</h2>
              <p className="text-[12px] text-muted">Segmentación por líneas de servicio</p>
            </div>
            <SampleBadge />
          </div>
          <DonutChart slices={DISTRIBUCION_CATEGORIA} centerValue="1,248.5" centerLabel="HRS TOTAL" />
        </div>

        <div className="card p-5">
          <h2 className="mb-1 font-semibold text-ink">Estado de tareas</h2>
          <p className="mb-3 text-[12px] text-muted">Pipeline operativo · {totalTareas} tareas totales</p>
          <div className="mb-4 flex h-2.5 w-full overflow-hidden rounded-full bg-field">
            {columnas.map((c) => (
              <div
                key={c.estado}
                className={COLUMN_TONE[c.estado]}
                style={{ width: totalTareas ? `${(c.total / totalTareas) * 100}%` : 0 }}
              />
            ))}
          </div>
          <div className="grid grid-cols-2 gap-3">
            {columnas.map((c) => (
              <div key={c.estado} className="rounded-lg bg-field/70 px-3 py-2.5">
                <p className="flex items-center gap-1.5 text-[12px] text-muted">
                  <span className={`size-2 rounded-full ${COLUMN_TONE[c.estado]}`} /> {c.titulo}
                </p>
                <p className="text-lg font-bold text-ink">{c.total}</p>
              </div>
            ))}
          </div>
          <Link to="/tablero" className="mt-4 inline-block text-[13px] font-medium text-navy-700 hover:underline">
            Ver tablero completo →
          </Link>
        </div>
      </div>
    </div>
  );
}
