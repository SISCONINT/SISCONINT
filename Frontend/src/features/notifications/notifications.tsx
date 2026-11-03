import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api } from "@/shared/api/client";
import { Loader2, Bell } from "lucide-react";

interface Notificacion {
  id: number;
  tipo: string;
  titulo: string;
  mensaje: string;
  entidad_tipo: string | null;
  entidad_id: number | null;
  enlace: string | null;
  leida: boolean;
  created_at: string;
}

interface NotificationsResponse {
  data: Notificacion[];
  meta?: { page: number; per_page: number; total: number; pages?: number; no_leidas?: number };
}

async function fetchNotifications(leida: boolean | null, page: number): Promise<NotificationsResponse> {
  const res = await api.get<NotificationsResponse>("/notifications", {
    params: { leida: leida === null ? undefined : leida, page },
  });
  return res.data;
}

export function NotificationsPage() {
  const queryClient = useQueryClient();
  const [filtro, setFiltro] = useState<"todas" | "no_leidas" | "leidas">("todas");
  const [page, setPage] = useState(1);

  const leidaParam = filtro === "no_leidas" ? false : filtro === "leidas" ? true : null;

  const query = useQuery({
    queryKey: ["notifications", "list", filtro, page],
    queryFn: () => fetchNotifications(leidaParam, page),
    staleTime: 15_000,
  });

  const items = query.data?.data ?? [];
  const meta = query.data?.meta;
  const noLeidas = meta?.no_leidas ?? 0;
  const totalPages = meta?.pages ?? Math.ceil((meta?.total ?? items.length) / (meta?.per_page ?? 20));

  const markRead = useMutation({
    mutationFn: async (id: number) => {
      const res = await api.patch(`/notifications/${id}/leida`);
      return res.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["notifications"] });
    },
  });

  const markAll = useMutation({
    mutationFn: async () => {
      const res = await api.patch("/notifications/leidas");
      return res.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["notifications"] });
    },
  });

  return (
    <div className="mx-auto flex w-full max-w-[1440px] flex-col gap-4">
      <header className="flex flex-col gap-2 sm:flex-row sm:items-end sm:justify-between">
        <div>
          <p className="text-[10px] font-semibold uppercase tracking-[0.16em] text-gold-700">
            Módulo 10 · Notificaciones
          </p>
          <h1 className="mt-1 font-display text-2xl font-bold text-ink sm:text-3xl">
            Notificaciones
          </h1>
          <p className="mt-1.5 max-w-2xl text-sm text-muted">
            Bandeja de notificaciones propias de los últimos 90 días.
          </p>
        </div>
        <div className="flex items-center gap-2">
          <span className="rounded-full bg-app px-3 py-1 text-xs font-semibold text-navy-800">
            {noLeidas} no leídas
          </span>
          <button
            type="button"
            onClick={() => markAll.mutate()}
            disabled={markAll.isPending || noLeidas === 0}
            className="rounded-lg border border-line px-3 py-2 text-xs font-semibold text-ink disabled:opacity-40"
          >
            Marcar todas como leídas
          </button>
        </div>
      </header>

      <div className="card flex flex-wrap items-center gap-3 p-3">
        <select
          value={filtro}
          onChange={(e) => {
            setFiltro(e.target.value as "todas" | "no_leidas" | "leidas");
            setPage(1);
          }}
          className="rounded-lg border border-line bg-surface px-3 py-2 text-sm text-ink"
        >
          <option value="todas">Todas</option>
          <option value="no_leidas">No leídas</option>
          <option value="leidas">Leídas</option>
        </select>
      </div>

      {query.isLoading && (
        <div className="card flex items-center justify-center gap-2 p-8 text-muted">
          <Loader2 size={18} className="animate-spin" />
          Cargando notificaciones…
        </div>
      )}

      {query.isError && (
        <div className="card p-6 text-center text-sm text-danger">
          No se pudo cargar la bandeja de notificaciones.
        </div>
      )}

      {!query.isLoading && !query.isError && items.length === 0 && (
        <div className="card flex flex-col items-center gap-3 px-6 py-12 text-center">
          <span className="grid size-12 place-items-center rounded-full bg-app text-navy-800">
            <Bell size={22} />
          </span>
          <p className="text-sm text-muted">Sin notificaciones para el filtro seleccionado.</p>
        </div>
      )}

      {!query.isLoading && !query.isError && items.length > 0 && (
        <section className="flex flex-col gap-2">
          {items.map((n) => (
            <article
              key={n.id}
              className={`card p-4 ${n.leida ? "opacity-70" : ""}`}
            >
              <div className="flex items-start justify-between gap-3">
                <div className="min-w-0">
                  <p className="text-sm font-semibold text-ink">{n.titulo}</p>
                  <p className="mt-1 text-xs text-muted">{n.mensaje}</p>
                  <p className="mt-1 text-[10px] text-muted">
                    {n.tipo} · {n.created_at}
                    {n.enlace ? ` · ${n.enlace}` : ""}
                  </p>
                </div>
                {!n.leida && (
                  <button
                    type="button"
                    onClick={() => markRead.mutate(n.id)}
                    disabled={markRead.isPending}
                    className="shrink-0 rounded-lg border border-line px-3 py-1.5 text-xs font-semibold text-ink disabled:opacity-40"
                  >
                    Marcar leída
                  </button>
                )}
              </div>
            </article>
          ))}
          <div className="flex items-center justify-between pt-2">
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