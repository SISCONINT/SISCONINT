import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { api } from "@/shared/api/client";
import { Loader2 } from "lucide-react";

interface BoardCard {
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
  minutos_registrados: number;
  horas_registradas: number;
  horas_estimadas: number | null;
  porcentaje_registrado: number | null;
  completada_en: string | null;
}

interface BoardColumn {
  estado: string;
  titulo: string;
  total: number;
  tareas: BoardCard[];
}

interface BoardResponse {
  data: {
    columnas: BoardColumn[];
    total_tareas: number;
    mensaje: string | null;
  };
}

async function fetchBoard(prioridad: string | null): Promise<BoardResponse["data"]> {
  const res = await api.get<BoardResponse>("/tasks/board", {
    params: { prioridad: prioridad || undefined },
  });
  return res.data.data;
}

export function KanbanBoardPage() {
  const [prioridad, setPrioridad] = useState<string | null>(null);

  const query = useQuery({
    queryKey: ["tasks", "board", prioridad],
    queryFn: () => fetchBoard(prioridad),
    staleTime: 15_000,
  });

  const board = query.data;

  return (
    <div className="mx-auto flex w-full max-w-[1440px] flex-col gap-4">
      <header className="flex flex-col gap-2 sm:flex-row sm:items-end sm:justify-between">
        <div>
          <p className="text-[10px] font-semibold uppercase tracking-[0.16em] text-gold-700">
            Módulo 6 · Tablero Kanban
          </p>
          <h1 className="mt-1 font-display text-2xl font-bold text-ink sm:text-3xl">
            Tablero Kanban
          </h1>
          <p className="mt-1.5 max-w-2xl text-sm text-muted">
            Visualización de tareas por estado con contadores y filtros.
          </p>
        </div>
        <select
          value={prioridad ?? ""}
          onChange={(e) => setPrioridad(e.target.value || null)}
          className="rounded-lg border border-line bg-surface px-3 py-2 text-sm text-ink"
        >
          <option value="">Todas las prioridades</option>
          {["BAJA", "MEDIA", "ALTA", "URGENTE"].map((p) => (
            <option key={p} value={p}>
              {p}
            </option>
          ))}
        </select>
      </header>

      {query.isLoading && (
        <div className="card flex items-center justify-center gap-2 p-8 text-muted">
          <Loader2 size={18} className="animate-spin" />
          Cargando tablero…
        </div>
      )}

      {query.isError && (
        <div className="card p-6 text-center text-sm text-danger">
          No se pudo cargar el tablero.
        </div>
      )}

      {board?.mensaje && (
        <div className="card p-4 text-center text-sm text-muted">{board.mensaje}</div>
      )}

      {!query.isLoading && !query.isError && board && (
        <section className="grid gap-3 md:grid-cols-2 xl:grid-cols-4">
          {board.columnas.map((col) => (
            <div key={col.estado} className="card flex flex-col gap-2 p-3">
              <header className="flex items-center justify-between">
                <h2 className="text-sm font-semibold text-ink">{col.titulo}</h2>
                <span className="rounded-full bg-app px-2 py-0.5 text-[10px] font-bold text-navy-800">
                  {col.total}
                </span>
              </header>
              <div className="flex flex-col gap-2">
                {col.tareas.map((t) => (
                  <article
                    key={t.id}
                    className="rounded-lg border border-line bg-surface p-3 text-xs"
                  >
                    <p className="font-semibold text-ink">{t.titulo}</p>
                    <p className="mt-1 text-muted">{t.cliente_nombre ?? t.cliente_id}</p>
                    <p className="mt-1 text-muted">
                      {t.asignado_nombre ?? t.asignado_id} · {t.prioridad}
                    </p>
                    <p className="mt-1 text-muted">
                      {t.fecha_limite}
                      {t.hora_limite ? ` ${t.hora_limite}` : ""}
                    </p>
                    <span className="mt-1 inline-block rounded-full bg-app px-2 py-0.5 text-[9.5px] font-semibold text-navy-800">
                      {t.semaforo}
                    </span>
                  </article>
                ))}
                {col.tareas.length === 0 && (
                  <p className="py-4 text-center text-[11px] text-muted">Sin tareas</p>
                )}
              </div>
            </div>
          ))}
        </section>
      )}
    </div>
  );
}