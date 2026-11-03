import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { api } from "@/shared/api/client";
import { Loader2, AlertTriangle } from "lucide-react";

interface AlertItem {
  id: number;
  titulo: string;
  cliente_id: number;
  cliente_nombre: string | null;
  asignado_id: number;
  asignado_nombre: string | null;
  prioridad: string;
  estado: string;
  fecha_limite: string;
  hora_limite: string | null;
  semaforo: string;
  dias_restantes: number;
  dias_atraso: number;
}

interface AlertsResponse {
  data: {
    conteos: Record<string, number>;
    tareas: AlertItem[];
  };
  meta?: { page: number; per_page: number; total: number; pages?: number };
}

async function fetchAlerts(color: string | null, page: number): Promise<AlertsResponse> {
  const res = await api.get<AlertsResponse>("/tasks/alerts", {
    params: { color: color || undefined, page },
  });
  return res.data;
}

export function AlertsPage() {
  const [color, setColor] = useState<string | null>(null);
  const [page, setPage] = useState(1);

  const query = useQuery({
    queryKey: ["tasks", "alerts", color, page],
    queryFn: () => fetchAlerts(color, page),
    staleTime: 15_000,
  });

  const data = query.data?.data;
  const items = data?.tareas ?? [];
  const meta = query.data?.meta;
  const totalPages = meta?.pages ?? Math.ceil((meta?.total ?? items.length) / (meta?.per_page ?? 20));

  return (
    <div className="mx-auto flex w-full max-w-[1440px] flex-col gap-4">
      <header className="flex flex-col gap-2 sm:flex-row sm:items-end sm:justify-between">
        <div>
          <p className="text-[10px] font-semibold uppercase tracking-[0.16em] text-gold-700">
            Módulo 9 · Semáforos y alertas de vencimiento
          </p>
          <h1 className="mt-1 font-display text-2xl font-bold text-ink sm:text-3xl">
            Alertas Fiscales
          </h1>
          <p className="mt-1.5 max-w-2xl text-sm text-muted">
            Panel de tareas en rojo y amarillo con atraso.
          </p>
        </div>
        <select
          value={color ?? ""}
          onChange={(e) => {
            setColor(e.target.value || null);
            setPage(1);
          }}
          className="rounded-lg border border-line bg-surface px-3 py-2 text-sm text-ink"
        >
          <option value="">Todos los colores</option>
          <option value="ROJO">Rojo</option>
          <option value="AMARILLO">Amarillo</option>
        </select>
      </header>

      {data?.conteos && (
        <div className="grid gap-3 sm:grid-cols-2">
          <div className="card p-4">
            <p className="text-[10px] font-semibold uppercase text-muted">Rojo</p>
            <p className="text-2xl font-bold text-danger">{data.conteos["ROJO"] ?? 0}</p>
          </div>
          <div className="card p-4">
            <p className="text-[10px] font-semibold uppercase text-muted">Amarillo</p>
            <p className="text-2xl font-bold text-amber-700">{data.conteos["AMARILLO"] ?? 0}</p>
          </div>
        </div>
      )}

      {query.isLoading && (
        <div className="card flex items-center justify-center gap-2 p-8 text-muted">
          <Loader2 size={18} className="animate-spin" />
          Cargando alertas…
        </div>
      )}

      {query.isError && (
        <div className="card p-6 text-center text-sm text-danger">
          No se pudo cargar el panel de alertas.
        </div>
      )}

      {!query.isLoading && !query.isError && items.length === 0 && (
        <div className="card flex flex-col items-center gap-3 px-6 py-12 text-center">
          <span className="grid size-12 place-items-center rounded-full bg-app text-navy-800">
            <AlertTriangle size={22} />
          </span>
          <p className="text-sm text-muted">Sin alertas para los filtros seleccionados.</p>
        </div>
      )}

      {!query.isLoading && !query.isError && items.length > 0 && (
        <section className="card overflow-x-auto">
          <table className="w-full text-left">
            <thead className="border-b border-line bg-app/60">
              <tr className="text-[10px] font-semibold uppercase tracking-[0.1em] text-muted">
                <th className="px-5 py-3">Título</th>
                <th className="px-4 py-3">Cliente</th>
                <th className="px-4 py-3">Asignado</th>
                <th className="px-4 py-3">Prioridad</th>
                <th className="px-4 py-3">Estado</th>
                <th className="px-4 py-3">Fecha límite</th>
                <th className="px-4 py-3">Semáforo</th>
                <th className="px-4 py-3">Días atraso</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-line">
              {items.map((t) => (
                <tr key={t.id} className="hover:bg-app/60">
                  <td className="px-5 py-3 text-sm font-semibold text-ink">{t.titulo}</td>
                  <td className="px-4 py-3 text-xs text-muted">{t.cliente_nombre ?? t.cliente_id}</td>
                  <td className="px-4 py-3 text-xs text-muted">{t.asignado_nombre ?? t.asignado_id}</td>
                  <td className="px-4 py-3 text-xs text-muted">{t.prioridad}</td>
                  <td className="px-4 py-3 text-xs text-muted">{t.estado}</td>
                  <td className="px-4 py-3 text-xs text-muted">
                    {t.fecha_limite}
                    {t.hora_limite ? ` ${t.hora_limite}` : ""}
                  </td>
                  <td className="px-4 py-3 text-xs text-muted">{t.semaforo}</td>
                  <td className="px-4 py-3 text-xs text-muted">{t.dias_atraso}</td>
                </tr>
              ))}
            </tbody>
          </table>
          <div className="flex items-center justify-between border-t border-line px-5 py-3">
            <button
              type="button"
              disabled={page <= 1}
              onClick={() => setPage((p) => Math.max(1, p - 1))}
              className="rounded-lg border border-line px-3 py-1.5 text-xs font-semibold text-ink disabled:opacity-40"
            >
              Anterior
            </button>
            <span className="text-xs text-muted">
              Página {page} de {Math.max(1, totalPages)}
            </span>
            <button
              type="button"
              disabled={page >= totalPages}
              onClick={() => setPage((p) => p + 1)}
              className="rounded-lg border border-line px-3 py-1.5 text-xs font-semibold text-ink disabled:opacity-40"
            >
              Siguiente
            </button>
          </div>
        </section>
      )}
    </div>
  );
}