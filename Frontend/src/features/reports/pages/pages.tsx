import { useMemo, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { FileText, Loader2, RefreshCw } from "lucide-react";
import { PERIODOS } from "@/shared/constants/constants";
import {
  ErrorState,
  LoadingState,
  Notice,
  PageHeader,
} from "@/shared/components/components";
import {
  formatDateTime,
  getErrorMessage,
  monthBounds,
  todayISO,
} from "@/shared/utils/utils";
import { fetchReportOptions, fetchReportSummary } from "../api/api";
import {
  ReportCategoryBreakdown,
  ReportClientBreakdown,
  ReportKpis,
  ReportTaskStatus,
  ReportTeamBreakdown,
} from "../components/components";
import { exportReportPdf } from "../pdf/reportPdf";
import type { ReportFilters, ReportOption } from "../types";

export function ReportsPage() {
  const initial = monthBounds();
  const [periodo, setPeriodo] = useState("MES_ACTUAL");
  const [fechaDesde, setFechaDesde] = useState(initial.desde);
  const [fechaHasta, setFechaHasta] = useState(initial.hasta);
  const [cliente, setCliente] = useState("");
  const [colaborador, setColaborador] = useState("");
  const [exportando, setExportando] = useState(false);
  const [errorExport, setErrorExport] = useState<string | null>(null);

  const clientsQuery = useQuery({
    queryKey: ["clients", "options", "reports"],
    queryFn: () => fetchReportOptions<ReportOption>("/clients/options"),
    staleTime: 60_000,
  });

  const usersQuery = useQuery({
    queryKey: ["users", "options", "reports"],
    queryFn: () => fetchReportOptions<ReportOption>("/users/options"),
    staleTime: 60_000,
  });

  const filters = useMemo<ReportFilters>(() => {
    const base: ReportFilters = { periodo };
    if (periodo === "PERSONALIZADO") {
      base.fecha_desde = fechaDesde;
      base.fecha_hasta = fechaHasta;
    }
    if (cliente) base.cliente = Number(cliente);
    if (colaborador) base.colaborador = Number(colaborador);
    return base;
  }, [periodo, fechaDesde, fechaHasta, cliente, colaborador]);

  const query = useQuery({
    queryKey: ["reports", "summary", filters],
    queryFn: () => fetchReportSummary(filters),
    staleTime: 30_000,
  });

  const data = query.data;

  const exportPdf = async () => {
    if (!data) return;
    setExportando(true);
    setErrorExport(null);
    try {
      await exportReportPdf(data);
    } catch (error) {
      setErrorExport(getErrorMessage(error));
    } finally {
      setExportando(false);
    }
  };

  return (
    <div className="mx-auto flex w-full max-w-[1440px] flex-col gap-4">
      <PageHeader
        eyebrow="Módulo 12 · Reportes ejecutivos"
        title="Reportes Ejecutivos"
        description="Resumen del periodo con horas, carga de trabajo, estado de tareas y costo estimado."
        actions={
          <>
            <button type="button" className="inline-flex items-center justify-center gap-2 rounded-lg border border-line bg-surface px-4 py-2.5 text-sm font-semibold text-ink transition hover:bg-app disabled:cursor-not-allowed disabled:opacity-60" onClick={() => query.refetch()} disabled={query.isFetching || exportando}>
              <RefreshCw size={16} className={query.isFetching ? "animate-spin" : ""} /> Actualizar
            </button>
            <button type="button" className="inline-flex items-center justify-center gap-2 rounded-lg bg-gold-300 px-4 py-2.5 text-sm font-semibold text-navy-900 transition hover:brightness-95 disabled:cursor-not-allowed disabled:opacity-60" onClick={exportPdf} disabled={!data || exportando}>
              {exportando ? <Loader2 size={16} className="animate-spin" /> : <FileText size={16} />}
              {exportando ? "Generando PDF…" : "Exportar PDF"}
            </button>
          </>
        }
      />

      {errorExport && (
        <Notice tone="danger">No se pudo generar el PDF: {errorExport}</Notice>
      )}

      {data?.sin_informacion && data.mensaje && <Notice tone="info">{data.mensaje}</Notice>}
      {query.isError && <ErrorState message={getErrorMessage(query.error)} />}

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

        <label className="flex min-w-48 flex-col gap-1">
          <span className="text-[10px] font-semibold uppercase tracking-wide text-muted">Cliente</span>
          <select
            value={cliente}
            onChange={(event) => setCliente(event.target.value)}
            className="rounded-lg border border-line bg-surface px-3 py-2 text-sm text-ink"
          >
            <option value="">Todos los clientes</option>
            {(clientsQuery.data ?? []).map((option) => (
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
            {(usersQuery.data ?? []).map((option) => (
              <option key={option.id} value={option.id}>
                {option.nombre_completo}
              </option>
            ))}
          </select>
        </label>

        {data && (
          <div className="ml-auto flex flex-col items-end gap-1 text-right">
            <span className="rounded-full bg-app px-3 py-1.5 text-[11px] font-medium text-muted">
              {data.periodo.etiqueta}: {data.periodo.desde} → {data.periodo.hasta}
            </span>
            <span className="text-[10px] text-muted">Generado {formatDateTime(data.generado_en)}</span>
          </div>
        )}
      </section>

      {query.isLoading && <LoadingState label="Generando reporte…" />}

      {data && (
        <>
          <ReportKpis data={data} />

          {data.filtros && (data.filtros.cliente_nombre || data.filtros.colaborador_nombre) && (
            <div className="flex flex-wrap gap-2 text-[11px]">
              {data.filtros.cliente_nombre && (
                <span className="rounded-full bg-app px-3 py-1 font-medium text-muted">
                  Cliente: {data.filtros.cliente_nombre}
                </span>
              )}
              {data.filtros.colaborador_nombre && (
                <span className="rounded-full bg-app px-3 py-1 font-medium text-muted">
                  Colaborador: {data.filtros.colaborador_nombre}
                </span>
              )}
            </div>
          )}

          <ReportTaskStatus estado={data.estado_tareas} />

          <section className="grid gap-3 xl:grid-cols-2">
            <ReportTeamBreakdown data={data} />
            <ReportClientBreakdown data={data} />
            <ReportCategoryBreakdown data={data} />
          </section>
        </>
      )}
    </div>
  );
}
