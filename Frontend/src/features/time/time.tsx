import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { api } from "@/shared/api/client";
import { Loader2, Timer } from "lucide-react";

interface TimeEntry {
  id: number;
  fecha: string;
  empleado_id: number;
  empleado_nombre: string | null;
  cliente_id: number | null;
  cliente_nombre: string | null;
  tarea_id: number;
  tarea_titulo: string | null;
  tipo: string;
  duracion_minutos: number;
  horas: number;
  descripcion: string;
  nivel_escalafon: string;
  cierre_automatico: boolean;
}

interface TimeEntriesResponse {
  data: TimeEntry[];
  meta?: { page: number; per_page: number; total: number; pages?: number };
}

async function fetchEntries(page: number): Promise<TimeEntriesResponse> {
  const res = await api.get<TimeEntriesResponse>("/time-entries", {
    params: { page },
  });
  return res.data;
}

export function TimeEntriesPage() {
  const [page, setPage] = useState(1);

  const query = useQuery({
    queryKey: ["time-entries", "list", page],
    queryFn: () => fetchEntries(page),
    staleTime: 15_000,
  });

  const items = query.data?.data ?? [];
  const meta = query.data?.meta;
  const totalPages = meta?.pages ?? Math.ceil((meta?.total ?? items.length) / (meta?.per_page ?? 20));

  return (
    <div className="mx-auto flex w-full max-w-[1440px] flex-col gap-4">
      <header className="flex flex-col gap-2 sm:flex-row sm:items-end sm:justify-between">
        <div>
          <p className="text-[10px] font-semibold uppercase tracking-[0.16em] text-gold-700">
            Módulo 8 · Registro de tiempos
          </p>
          <h1 className="mt-1 font-display text-2xl font-bold text-ink sm:text-3xl">
            Registro de Tiempos
          </h1>
          <p className="mt-1.5 max-w-2xl text-sm text-muted">
            Consulta de registros de tiempo del despacho con alcance por rol.
          </p>
        </div>
      </header>

      {query.isLoading && (
        <div className="card flex items-center justify-center gap-2 p-8 text-muted">
          <Loader2 size={18} className="animate-spin" />
          Cargando registros…
        </div>
      )}

      {query.isError && (
        <div className="card p-6 text-center text-sm text-danger">
          No se pudo cargar el registro de tiempos.
        </div>
      )}

      {!query.isLoading && !query.isError && items.length === 0 && (
        <div className="card flex flex-col items-center gap-3 px-6 py-12 text-center">
          <span className="grid size-12 place-items-center rounded-full bg-app text-navy-800">
            <Timer size={22} />
          </span>
          <p className="text-sm text-muted">Sin registros de tiempo para el filtro actual.</p>
        </div>
      )}

      {!query.isLoading && !query.isError && items.length > 0 && (
        <section className="card overflow-x-auto">
          <table className="w-full text-left">
            <thead className="border-b border-line bg-app/60">
              <tr className="text-[10px] font-semibold uppercase tracking-[0.1em] text-muted">
                <th className="px-5 py-3">Fecha</th>
                <th className="px-4 py-3">Empleado</th>
                <th className="px-4 py-3">Cliente</th>
                <th className="px-4 py-3">Tarea</th>
                <th className="px-4 py-3">Tipo</th>
                <th className="px-4 py-3">Duración</th>
                <th className="px-4 py-3">Descripción</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-line">
              {items.map((e) => (
                <tr key={e.id} className="hover:bg-app/60">
                  <td className="px-5 py-3 text-xs text-muted">{e.fecha}</td>
                  <td className="px-4 py-3 text-xs text-muted">{e.empleado_nombre ?? e.empleado_id}</td>
                  <td className="px-4 py-3 text-xs text-muted">{e.cliente_nombre ?? e.cliente_id ?? "—"}</td>
                  <td className="px-4 py-3 text-xs text-muted">{e.tarea_titulo ?? e.tarea_id}</td>
                  <td className="px-4 py-3 text-xs text-muted">{e.tipo}</td>
                  <td className="px-4 py-3 text-xs text-muted">{e.horas} hrs</td>
                  <td className="px-4 py-3 text-xs text-muted">{e.descripcion}</td>
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