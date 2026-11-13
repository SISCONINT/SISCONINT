import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useNavigate } from "react-router-dom";
import { Columns3, GripVertical, Loader2, Plus } from "lucide-react";
import { api } from "@/shared/api/client";
import { ApiError } from "@/shared/api/types";
import {
  ESTADO_BADGE,
  ESTADO_LABELS,
  PRIORIDAD_BADGE,
  PRIORIDAD_LABELS,
  PRIORIDADES,
  SEMAFORO_BADGE,
  SEMAFORO_LABELS,
} from "@/shared/constants/constants";
import { Badge, EmptyState, ErrorState, LoadingState, PageHeader } from "@/shared/components/components";
import { formatDate, formatHours, getErrorMessage } from "@/shared/utils/utils";

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

interface BoardData {
  columnas: BoardColumn[];
  total_tareas: number;
  mensaje: string | null;
}

interface Option {
  id: number;
  nombre_completo: string;
}

interface OptionsResponse<T> {
  data: T[];
}

async function fetchBoard(params: Record<string, string | number | undefined>): Promise<BoardData> {
  const res = await api.get<{ data: BoardData }>("/tasks/board", { params });
  return res.data.data;
}

async function fetchOptions<T>(url: string): Promise<T[]> {
  const res = await api.get<OptionsResponse<T>>(url);
  return res.data.data ?? [];
}

export function KanbanBoardPage() {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const [prioridad, setPrioridad] = useState("");
  const [cliente, setCliente] = useState("");
  const [responsable, setResponsable] = useState("");
  const [draggingId, setDraggingId] = useState<number | null>(null);
  const [overColumn, setOverColumn] = useState<string | null>(null);
  const [errorMessage, setErrorMessage] = useState("");

  const params = {
    prioridad: prioridad || undefined,
    cliente: cliente ? Number(cliente) : undefined,
    responsable: responsable ? Number(responsable) : undefined,
  };

  const boardQuery = useQuery({
    queryKey: ["tasks", "board", params],
    queryFn: () => fetchBoard(params),
    staleTime: 15_000,
  });

  const clientsQuery = useQuery({
    queryKey: ["clients", "options", "kanban"],
    queryFn: () => fetchOptions<Option>("/clients/options"),
    staleTime: 60_000,
  });

  const usersQuery = useQuery({
    queryKey: ["users", "options", "kanban"],
    queryFn: () => fetchOptions<Option>("/users/options"),
    staleTime: 60_000,
  });

  const moveMutation = useMutation({
    mutationFn: async ({ id, estado, confirmar }: { id: number; estado: string; confirmar: boolean }) => {
      await api.patch(`/tasks/${id}/estado`, {
        estado,
        confirmar_subtareas_pendientes: confirmar,
      });
    },
    onSuccess: () => {
      setErrorMessage("");
      queryClient.invalidateQueries({ queryKey: ["tasks"] });
    },
    onError: (error, variables) => {
      if (error instanceof ApiError && error.status === 409) {
        if (window.confirm(`${error.message}\n\n¿Mover la tarea de todos modos?`)) {
          moveMutation.mutate({ ...variables, confirmar: true });
          return;
        }
        setErrorMessage(error.message);
        return;
      }
      setErrorMessage(getErrorMessage(error));
    },
  });

  const requestMove = (id: number, estado: string, from: string) => {
    if (estado === from) return;
    moveMutation.mutate({ id, estado, confirmar: false });
  };

  const columns = boardQuery.data?.columnas ?? [];

  return (
    <div className="mx-auto flex w-full max-w-[1440px] flex-col gap-4">
      <PageHeader
        eyebrow="Módulo 6 · Tablero Kanban"
        title="Tablero Kanban"
        description="Arrastra una tarjeta a otra columna para cambiar su estado. Los filtros se combinan con el alcance por rol."
        actions={
          <button type="button" className="inline-flex items-center gap-2 rounded-lg border border-line bg-surface px-4 py-2.5 text-sm font-semibold text-ink" onClick={() => navigate("/tareas")}>
            <Plus size={16} /> Ver listado
          </button>
        }
      />

      <section className="card flex flex-wrap items-center gap-3 p-3">
        <select value={prioridad} onChange={(event) => setPrioridad(event.target.value)} className="rounded-lg border border-line bg-surface px-3 py-2 text-sm text-ink">
          <option value="">Todas las prioridades</option>
          {PRIORIDADES.map((item) => (
            <option key={item} value={item}>{PRIORIDAD_LABELS[item]}</option>
          ))}
        </select>
        <select value={cliente} onChange={(event) => setCliente(event.target.value)} className="rounded-lg border border-line bg-surface px-3 py-2 text-sm text-ink">
          <option value="">Todos los clientes</option>
          {(clientsQuery.data ?? []).map((option) => (
            <option key={option.id} value={option.id}>{option.nombre_completo}</option>
          ))}
        </select>
        <select value={responsable} onChange={(event) => setResponsable(event.target.value)} className="rounded-lg border border-line bg-surface px-3 py-2 text-sm text-ink">
          <option value="">Todos los responsables</option>
          {(usersQuery.data ?? []).map((option) => (
            <option key={option.id} value={option.id}>{option.nombre_completo}</option>
          ))}
        </select>
        <span className="ml-auto text-xs text-muted">
          {boardQuery.data?.total_tareas ?? 0} tareas · arrastra para mover
        </span>
      </section>

      {errorMessage && (
        <p className="rounded-xl border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-700" role="alert">
          {errorMessage}
        </p>
      )}

      {boardQuery.isLoading && <LoadingState label="Cargando tablero…" />}
      {boardQuery.isError && <ErrorState message={getErrorMessage(boardQuery.error)} />}
      {boardQuery.data?.mensaje && <p className="card p-4 text-center text-sm text-muted">{boardQuery.data.mensaje}</p>}

      {!boardQuery.isLoading && !boardQuery.isError && columns.length > 0 && (
        <section className="grid gap-3 md:grid-cols-2 xl:grid-cols-4">
          {columns.map((column) => {
            const isOver = overColumn === column.estado;
            return (
              <div
                key={column.estado}
                className={`card flex min-h-72 flex-col gap-2 p-3 transition ${isOver ? "ring-2 ring-gold-500 ring-offset-2" : ""}`}
                onDragOver={(event) => {
                  event.preventDefault();
                  event.dataTransfer.dropEffect = "move";
                  setOverColumn(column.estado);
                }}
                onDragLeave={(event) => {
                  if (!event.currentTarget.contains(event.relatedTarget as Node)) setOverColumn(null);
                }}
                onDrop={(event) => {
                  event.preventDefault();
                  setOverColumn(null);
                  const id = Number(event.dataTransfer.getData("text/plain"));
                  const card = columns.flatMap((item) => item.tareas).find((item) => item.id === id);
                  if (card) requestMove(card.id, column.estado, card.estado);
                  setDraggingId(null);
                }}
              >
                <header className="flex items-center justify-between gap-2">
                  <div className="flex items-center gap-2">
                    <span className={`size-2 rounded-full ${column.estado === "COMPLETADO" ? "bg-emerald-500" : column.estado === "EN_PROGRESO" ? "bg-sky-500" : column.estado === "EN_REVISION" ? "bg-amber-500" : "bg-slate-400"}`} />
                    <h2 className="text-sm font-semibold text-ink">{column.titulo}</h2>
                  </div>
                  <span className="rounded-full bg-app px-2 py-0.5 text-[10px] font-bold text-navy-800">{column.total}</span>
                </header>

                <div className="flex flex-1 flex-col gap-2">
                  {column.tareas.map((task) => (
                    <article
                      key={task.id}
                      draggable
                      onDragStart={(event) => {
                        event.dataTransfer.setData("text/plain", String(task.id));
                        event.dataTransfer.effectAllowed = "move";
                        setDraggingId(task.id);
                      }}
                      onDragEnd={() => {
                        setDraggingId(null);
                        setOverColumn(null);
                      }}
                      onClick={() => navigate(`/tareas/${task.id}`)}
                      className={`cursor-grab rounded-xl border border-line bg-surface p-3 text-xs shadow-sm transition hover:border-navy-900/20 active:cursor-grabbing ${draggingId === task.id ? "opacity-40" : ""}`}
                    >
                      <div className="flex items-start justify-between gap-2">
                        <p className="font-semibold leading-snug text-ink">{task.titulo}</p>
                        <GripVertical size={14} className="shrink-0 text-muted/60" />
                      </div>
                      <p className="mt-1 text-muted">{task.cliente_nombre ?? task.cliente_id}</p>
                      <p className="mt-0.5 text-muted">{task.asignado_nombre ?? task.asignado_id}</p>
                      <div className="mt-2 flex flex-wrap items-center gap-1.5">
                        <Badge className={PRIORIDAD_BADGE[task.prioridad]}>{PRIORIDAD_LABELS[task.prioridad] ?? task.prioridad}</Badge>
                        <Badge className={SEMAFORO_BADGE[task.semaforo]}>{SEMAFORO_LABELS[task.semaforo] ?? task.semaforo}</Badge>
                        <Badge className={ESTADO_BADGE[task.estado]}>{ESTADO_LABELS[task.estado] ?? task.estado}</Badge>
                      </div>
                      <div className="mt-2 flex items-center justify-between text-[10px] text-muted">
                        <span>{formatDate(task.fecha_limite)}</span>
                        <span>{formatHours(task.minutos_registrados)}{task.horas_estimadas ? ` / ${task.horas_estimadas} h` : ""}</span>
                      </div>
                      {task.porcentaje_registrado !== null && (
                        <div className="mt-1.5 h-1 overflow-hidden rounded-full bg-app">
                          <div className="h-full rounded-full bg-gold-500" style={{ width: `${Math.min(100, task.porcentaje_registrado)}%` }} />
                        </div>
                      )}
                    </article>
                  ))}
                  {column.tareas.length === 0 && (
                    <div className="flex flex-1 flex-col items-center justify-center gap-2 rounded-lg border border-dashed border-line py-6 text-center text-[11px] text-muted">
                      <Columns3 size={18} />
                      {isOver ? "Suelta aquí para mover" : "Sin tareas"}
                    </div>
                  )}
                </div>
              </div>
            );
          })}
        </section>
      )}

      {!boardQuery.isLoading && !boardQuery.isError && columns.length === 0 && (
        <EmptyState title="Sin columnas para mostrar" description="Revisa los filtros seleccionados." icon={<Columns3 size={22} />} />
      )}

      {moveMutation.isPending && (
        <div className="fixed bottom-4 right-4 flex items-center gap-2 rounded-lg bg-navy-900 px-4 py-2 text-xs font-semibold text-white shadow-lg">
          <Loader2 size={14} className="animate-spin" /> Moviendo tarea…
        </div>
      )}
    </div>
  );
}
