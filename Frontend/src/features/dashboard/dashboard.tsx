import { useMemo, useState, type ReactNode } from "react";
import { useQuery } from "@tanstack/react-query";
import { Link } from "react-router-dom";
import {
  AlertTriangle,
  BarChart3,
  CheckCircle2,
  Clock3,
  DollarSign,
  LayoutDashboard,
  ListChecks,
  Users,
} from "lucide-react";
import { api } from "@/shared/api/client";
import { useAuthStore } from "@/shared/auth/authStore";
import { ROLES } from "@/shared/constants/roles";
import { PERIODOS } from "@/shared/constants/constants";
import {
  ErrorState,
  LoadingState,
  Notice,
  PageHeader,
  StatCard,
} from "@/shared/components/components";
import {
  formatHours,
  formatMoney,
  getErrorMessage,
  monthBounds,
  todayISO,
} from "@/shared/utils/utils";

interface HorasCard {
  horas: number;
  minutos: number;
  variacion_porcentaje: number | null;
  horas_periodo_anterior: number;
}

interface CostoEstimado {
  disponible: boolean;
  monto: number | null;
  horas_sin_tarifa: number;
  mensaje: string;
}

interface DashboardData {
  periodo: { tipo: string; etiqueta: string; desde: string; hasta: string };
  periodo_anterior?: { desde: string; hasta: string };
  filtros?: {
    cliente_id: number | null;
    cliente_nombre: string | null;
    colaborador_id: number | null;
    colaborador_nombre: string | null;
  };
  tarjetas: {
    horas_totales: HorasCard;
    tareas_activas: number;
    tareas_vencidas: number;
    costo_estimado?: CostoEstimado | null;
  };
  tiempo_por_empleado?: Array<{ colaborador_id: number; nombre: string; minutos: number; horas: number }>;
  tiempo_por_cliente?: Array<{ cliente_id: number; nombre: string; minutos: number; horas: number }>;
  distribucion_por_categoria?: Array<{
    categoria_id: number;
    nombre: string;
    minutos: number;
    horas: number;
    porcentaje: number;
  }>;
  estado_tareas: Record<string, number>;
  sin_informacion: boolean;
  mensaje: string | null;
}

interface Option {
  id: number;
  nombre_completo: string;
}

interface OptionsResponse<T> {
  data: T[];
}

async function fetchDashboard(
  personal: boolean,
  params: Record<string, string | number | undefined>,
): Promise<DashboardData> {
  const res = await api.get<{ data: DashboardData }>(
    personal ? "/dashboard/me" : "/dashboard",
    { params },
  );
  return res.data.data;
}

function Bars({
  title,
  icon,
  rows,
  empty,
}: {
  title: string;
  icon: ReactNode;
  rows: Array<{ id: number; label: string; minutos: number; extra?: string }>;
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

export function DashboardPage() {
  const user = useAuthStore((state) => state.user);
  const personal = user?.rol === ROLES.CONTADOR;
  const canSeeTeam = !personal;

  const initial = monthBounds();
  const [periodo, setPeriodo] = useState("MES_ACTUAL");
  const [fechaDesde, setFechaDesde] = useState(initial.desde);
  const [fechaHasta, setFechaHasta] = useState(initial.hasta);
  const [cliente, setCliente] = useState("");
  const [colaborador, setColaborador] = useState("");

  const clientesQuery = useQuery({
    queryKey: ["clients", "options", "dashboard"],
    queryFn: async () => {
      const res = await api.get<OptionsResponse<Option>>("/clients/options");
      return res.data.data ?? [];
    },
    enabled: canSeeTeam,
    staleTime: 60_000,
  });

  const usuariosQuery = useQuery({
    queryKey: ["users", "options", "dashboard"],
    queryFn: async () => {
      const res = await api.get<OptionsResponse<Option>>("/users/options");
      return res.data.data ?? [];
    },
    enabled: canSeeTeam,
    staleTime: 60_000,
  });

  const params = useMemo(() => {
    const query: Record<string, string | number | undefined> = { periodo };
    if (periodo === "PERSONALIZADO") {
      query.fecha_desde = fechaDesde;
      query.fecha_hasta = fechaHasta;
    }
    if (canSeeTeam && cliente) query.cliente = Number(cliente);
    if (canSeeTeam && colaborador) query.colaborador = Number(colaborador);
    return query;
  }, [periodo, fechaDesde, fechaHasta, cliente, colaborador, canSeeTeam]);

  const query = useQuery({
    queryKey: ["dashboard", personal ? "me" : "team", params],
    queryFn: () => fetchDashboard(personal, params),
    staleTime: 30_000,
  });

  const data = query.data;
  const tarjetas = data?.tarjetas;
  const costo = tarjetas?.costo_estimado;

  const estadoRows = useMemo(() => {
    const estados = data?.estado_tareas ?? {};
    return [
      { key: "POR_HACER", label: "Por hacer", value: estados.POR_HACER ?? 0, color: "bg-slate-400" },
      { key: "EN_PROGRESO", label: "En progreso", value: estados.EN_PROGRESO ?? 0, color: "bg-sky-500" },
      { key: "EN_REVISION", label: "En revisión", value: estados.EN_REVISION ?? 0, color: "bg-amber-500" },
      { key: "COMPLETADO", label: "Completado", value: estados.COMPLETADO ?? 0, color: "bg-emerald-500" },
    ];
  }, [data]);

  return (
    <div className="mx-auto flex w-full max-w-[1440px] flex-col gap-4">
      <PageHeader
        eyebrow="Módulo 12 · Dashboard"
        title={personal ? "Mi Dashboard" : "Dashboard del Despacho"}
        description={
          personal
            ? "Tus horas, clientes y tareas del periodo seleccionado."
            : "Indicadores de horas, carga de trabajo y estado de las tareas del despacho."
        }
        actions={
          <Link
            to="/reportes"
            className="inline-flex items-center gap-2 rounded-lg border border-line bg-surface px-4 py-2.5 text-sm font-semibold text-ink transition hover:bg-app"
          >
            <BarChart3 size={16} /> Reportes
          </Link>
        }
      />

      <section className="card flex flex-wrap items-end gap-3 p-3">
        <label className="flex min-w-40 flex-col gap-1">
          <span className="text-[10px] font-semibold uppercase tracking-wide text-muted">Periodo</span>
          <select
            value={periodo}
            onChange={(event) => setPeriodo(event.target.value)}
            className="rounded-lg border border-line bg-surface px-3 py-2 text-sm text-ink"
          >
            {PERIODOS.map((item) => (
              <option key={item.value} value={item.value}>
                {item.label}
              </option>
            ))}
          </select>
        </label>

        {periodo === "PERSONALIZADO" && (
          <>
            <label className="flex flex-col gap-1">
              <span className="text-[10px] font-semibold uppercase tracking-wide text-muted">Desde</span>
              <input
                type="date"
                value={fechaDesde}
                max={fechaHasta || todayISO()}
                onChange={(event) => setFechaDesde(event.target.value)}
                className="rounded-lg border border-line bg-surface px-3 py-2 text-sm text-ink"
              />
            </label>
            <label className="flex flex-col gap-1">
              <span className="text-[10px] font-semibold uppercase tracking-wide text-muted">Hasta</span>
              <input
                type="date"
                value={fechaHasta}
                min={fechaDesde}
                onChange={(event) => setFechaHasta(event.target.value)}
                className="rounded-lg border border-line bg-surface px-3 py-2 text-sm text-ink"
              />
            </label>
          </>
        )}

        {canSeeTeam && (
          <>
            <label className="flex min-w-48 flex-col gap-1">
              <span className="text-[10px] font-semibold uppercase tracking-wide text-muted">Cliente</span>
              <select
                value={cliente}
                onChange={(event) => setCliente(event.target.value)}
                className="rounded-lg border border-line bg-surface px-3 py-2 text-sm text-ink"
              >
                <option value="">Todos los clientes</option>
                {(clientesQuery.data ?? []).map((option) => (
                  <option key={option.id} value={option.id}>
                    {option.nombre_completo}
                  </option>
                ))}
              </select>
            </label>
            <label className="flex min-w-48 flex-col gap-1">
              <span className="text-[10px] font-semibold uppercase tracking-wide text-muted">Colaborador</span>
              <select
                value={colaborador}
                onChange={(event) => setColaborador(event.target.value)}
                className="rounded-lg border border-line bg-surface px-3 py-2 text-sm text-ink"
              >
                <option value="">Todo el equipo</option>
                {(usuariosQuery.data ?? []).map((option) => (
                  <option key={option.id} value={option.id}>
                    {option.nombre_completo}
                  </option>
                ))}
              </select>
            </label>
          </>
        )}

        {data && (
          <span className="ml-auto rounded-full bg-app px-3 py-1.5 text-[11px] font-medium text-muted">
            {data.periodo.etiqueta}: {data.periodo.desde} → {data.periodo.hasta}
          </span>
        )}
      </section>

      {query.isLoading && <LoadingState label="Calculando indicadores…" />}
      {query.isError && <ErrorState message={getErrorMessage(query.error)} />}

      {data && (
        <>
          {data.sin_informacion && data.mensaje && <Notice tone="info">{data.mensaje}</Notice>}

          <section className="grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
            <StatCard
              label="Horas registradas"
              value={`${tarjetas?.horas_totales.horas ?? 0} h`}
              hint={
                tarjetas?.horas_totales.variacion_porcentaje === null
                  ? "Sin periodo anterior comparable"
                  : `${tarjetas?.horas_totales.variacion_porcentaje ?? 0}% vs. periodo anterior`
              }
              icon={<Clock3 size={18} />}
            />
            <StatCard
              label="Tareas activas"
              value={tarjetas?.tareas_activas ?? 0}
              hint="Sin contar completadas"
              icon={<ListChecks size={18} />}
            />
            <StatCard
              label="Tareas vencidas"
              value={tarjetas?.tareas_vencidas ?? 0}
              hint="Requieren atención"
              icon={<AlertTriangle size={18} />}
              tone={(tarjetas?.tareas_vencidas ?? 0) > 0 ? "danger" : "success"}
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

          <section className="card p-4">
            <header className="flex items-center gap-2">
              <span className="grid size-8 place-items-center rounded-lg bg-app text-navy-800">
                <CheckCircle2 size={17} />
              </span>
              <h2 className="text-sm font-semibold text-ink">Estado actual de tareas</h2>
              <span className="ml-auto text-xs text-muted">
                {data.estado_tareas.total ?? 0} tareas
              </span>
            </header>
            <div className="mt-4 grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
              {estadoRows.map((row) => (
                <div key={row.key} className="rounded-xl border border-line bg-app/40 p-3">
                  <div className="flex items-center gap-2">
                    <span className={`size-2 rounded-full ${row.color}`} />
                    <span className="text-xs font-medium text-muted">{row.label}</span>
                  </div>
                  <p className="mt-1 font-display text-xl font-bold text-ink">{row.value}</p>
                </div>
              ))}
            </div>
            {(data.estado_tareas.vencidas ?? 0) > 0 && (
              <p className="mt-3 text-xs font-medium text-danger">
                {data.estado_tareas.vencidas} tareas vencidas sin completar.
              </p>
            )}
          </section>

          <section className="grid gap-3 xl:grid-cols-2">
            {canSeeTeam && (
              <Bars
                title="Horas por colaborador"
                icon={<Users size={17} />}
                rows={(data.tiempo_por_empleado ?? []).map((row) => ({
                  id: row.colaborador_id,
                  label: row.nombre,
                  minutos: row.minutos,
                }))}
                empty="Sin horas registradas en el periodo."
              />
            )}
            <Bars
              title="Horas por cliente"
              icon={<LayoutDashboard size={17} />}
              rows={(data.tiempo_por_cliente ?? []).map((row) => ({
                id: row.cliente_id,
                label: row.nombre,
                minutos: row.minutos,
              }))}
              empty="Sin horas registradas en el periodo."
            />
            <Bars
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
          </section>
        </>
      )}
    </div>
  );
}
