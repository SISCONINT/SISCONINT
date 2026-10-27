import { Link } from "react-router-dom";
import { AlertTriangle, CheckCircle2, Clock, ListChecks, Plus } from "lucide-react";
import { PageHeader } from "@/shared/components/PageHeader";
import { PrioridadBadge } from "@/shared/components/Badge";
import { formatDate } from "@/shared/utils/format";
import { useTaskBoard, useTasks } from "@/features/tasks/api/useTasks";
import { StatCard } from "../components/StatCard";
import { BarRow } from "../components/BarRow";
import { DonutChart } from "../components/DonutChart";
import { SampleBadge } from "../components/SampleBadge";
import { CUMPLIMIENTO_PLAZOS, MIS_HORAS_POR_CATEGORIA, MIS_HORAS_POR_CLIENTE, MIS_HORAS_REGISTRADAS } from "../mockData";

const COLUMN_TONE: Record<string, string> = {
  POR_HACER: "bg-muted",
  EN_PROGRESO: "bg-navy-700",
  EN_REVISION: "bg-amber-500",
  COMPLETADO: "bg-emerald-500",
};

export function ContadorDashboard() {
  const { data: board, isLoading } = useTaskBoard({});
  const { data: listado } = useTasks({ page: 1 });

  const columnas = board?.columnas ?? [];
  const activas = columnas.filter((c) => c.estado !== "COMPLETADO").reduce((acc, c) => acc + c.total, 0);
  const vencidas = columnas
    .filter((c) => c.estado !== "COMPLETADO")
    .reduce((acc, c) => acc + c.tareas.filter((t) => t.semaforo === "ROJO").length, 0);

  const proximas = (listado?.data ?? [])
    .filter((t) => t.estado !== "COMPLETADO")
    .sort((a, b) => a.fecha_limite.localeCompare(b.fecha_limite))
    .slice(0, 4);

  return (
    <div>
      <PageHeader
        title="Mi Panel Operativo y Desempeño"
        subtitle="Seguimiento individual de tus tareas asignadas y próximos vencimientos."
        actions={
          <Link to="/tareas/nuevo" className="flex items-center gap-2 rounded-lg bg-gold-300 px-4 py-2.5 text-sm font-semibold text-ink hover:brightness-95">
            <Plus size={16} /> Nueva tarea
          </Link>
        }
      />

      <div className="mb-5 grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-4">
        <StatCard
          icon={Clock}
          label="Mis horas registradas (ejemplo)"
          value={`${MIS_HORAS_REGISTRADAS.horas} hrs`}
          hint={`Meta: ${MIS_HORAS_REGISTRADAS.meta} hrs · Facturables: ${MIS_HORAS_REGISTRADAS.facturables} hrs`}
        />
        <StatCard
          icon={ListChecks}
          label="Mis tareas activas"
          value={isLoading ? "…" : activas}
          hint="Distribuidas entre tus clientes asignados"
        />
        <StatCard
          icon={AlertTriangle}
          label="Atención inmediata"
          value={isLoading ? "…" : vencidas}
          tone={vencidas > 0 ? "danger" : "default"}
          hint="Tareas con semáforo rojo"
        />
        <StatCard
          icon={CheckCircle2}
          label="Cumplimiento de plazos (ejemplo)"
          value={`${CUMPLIMIENTO_PLAZOS.porcentaje}%`}
          hint={`${CUMPLIMIENTO_PLAZOS.aTiempo} de ${CUMPLIMIENTO_PLAZOS.total} entregas a tiempo`}
        />
      </div>

      <div className="mb-5 grid grid-cols-1 gap-5 lg:grid-cols-2">
        <div className="card p-5">
          <div className="mb-3 flex items-center justify-between">
            <div>
              <h2 className="font-semibold text-ink">Mis horas por cliente asignado</h2>
              <p className="text-[12px] text-muted">Distribución del tiempo registrado</p>
            </div>
            <SampleBadge />
          </div>
          <div className="flex flex-col gap-3.5">
            {MIS_HORAS_POR_CLIENTE.map((c, i) => (
              <BarRow key={c.nombre} title={`${i + 1}. ${c.nombre}`} value={`${c.horas.toFixed(1)} hrs (${c.porcentaje}%)`} percent={c.porcentaje} />
            ))}
          </div>
        </div>

        <div className="card p-5">
          <h2 className="mb-1 font-semibold text-ink">Pipeline de mis tareas</h2>
          <p className="mb-3 text-[12px] text-muted">{board?.total_tareas ?? "…"} tareas asignadas</p>
          <div className="mb-4 flex h-2.5 w-full overflow-hidden rounded-full bg-field">
            {columnas.map((c) => (
              <div key={c.estado} className={COLUMN_TONE[c.estado]} style={{ width: board?.total_tareas ? `${(c.total / board.total_tareas) * 100}%` : 0 }} />
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
          <Link to="/tareas" className="mt-4 inline-block text-[13px] font-medium text-navy-700 hover:underline">
            Ver todas mis tareas →
          </Link>
        </div>
      </div>

      <div className="grid grid-cols-1 gap-5 lg:grid-cols-2">
        <div className="card p-5">
          <div className="mb-3 flex items-center justify-between">
            <div>
              <h2 className="font-semibold text-ink">Mis horas por categoría fiscal</h2>
              <p className="text-[12px] text-muted">Especialidad de actividades operativas</p>
            </div>
            <SampleBadge />
          </div>
          <DonutChart slices={MIS_HORAS_POR_CATEGORIA} centerValue={`${MIS_HORAS_REGISTRADAS.horas}`} centerLabel="HRS TOTALES" />
        </div>

        <div className="card p-5">
          <h2 className="mb-1 font-semibold text-ink">Obligaciones inmediatas</h2>
          <p className="mb-3 text-[12px] text-muted">Tus próximos vencimientos</p>
          {proximas.length === 0 ? (
            <p className="text-sm text-muted">No tienes tareas pendientes próximas a vencer.</p>
          ) : (
            <ul className="flex flex-col gap-2.5">
              {proximas.map((t) => (
                <li key={t.id} className="rounded-lg bg-field/60 px-3 py-2.5">
                  <div className="flex items-center justify-between gap-2">
                    <p className="text-[11px] font-semibold uppercase tracking-wide text-muted">{t.cliente_nombre}</p>
                    <PrioridadBadge prioridad={t.prioridad} />
                  </div>
                  <p className="text-sm font-semibold text-ink">{t.titulo}</p>
                  <div className="mt-1 flex items-center justify-between text-[12px] text-muted">
                    <span>{formatDate(t.fecha_limite)}</span>
                    <Link to={`/tareas/${t.id}`} className="font-medium text-navy-700 hover:underline">
                      Ver tarea →
                    </Link>
                  </div>
                </li>
              ))}
            </ul>
          )}
        </div>
      </div>
    </div>
  );
}
