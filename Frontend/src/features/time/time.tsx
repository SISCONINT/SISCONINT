import { useEffect, useMemo, useState, type FormEvent } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Clock3, Loader2, Pencil, Play, Square, Timer } from "lucide-react";
import { api } from "@/shared/api/client";
import { useAuthStore } from "@/shared/auth/authStore";
import { ROLES } from "@/shared/constants/roles";
import {
  BTN_GHOST,
  BTN_PRIMARY,
  BTN_SECONDARY,
  INPUT_CLASS,
} from "@/shared/constants/constants";
import {
  EmptyState,
  ErrorState,
  FormField,
  LoadingState,
  Modal,
  ModalActions,
  Notice,
  PageHeader,
} from "@/shared/components/components";
import { Pagination } from "@/shared/components/Pagination";
import {
  formatDate,
  formatMinutes,
  getErrorMessage,
  todayISO,
  toISO,
} from "@/shared/utils/utils";

const PER_PAGE = 20;

interface TaskOption {
  id: number;
  titulo: string;
  cliente_id: number;
  cliente_nombre: string | null;
  estado: string;
  fecha_limite: string;
}

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
}

interface TimerData {
  id: number;
  tarea_id: number;
  tarea_titulo: string | null;
  cliente_id: number | null;
  cliente_nombre: string | null;
  transcurrido_segundos: number;
  transcurrido: string;
}

interface TimerState {
  activo: TimerData | null;
  aviso_cierre_automatico: { mensaje: string } | null;
}

interface TimeMeta {
  page: number;
  per_page: number;
  total: number;
  total_horas?: number;
  total_minutos?: number;
}

function weekBounds() {
  const now = new Date();
  const offset = (now.getDay() + 6) % 7;
  const monday = new Date(now);
  monday.setDate(now.getDate() - offset);
  const sunday = new Date(monday);
  sunday.setDate(monday.getDate() + 6);
  return { desde: toISO(monday), hasta: toISO(sunday) };
}

function formatClock(seconds: number) {
  const safe = Math.max(0, Math.floor(seconds));
  const hours = Math.floor(safe / 3600);
  const minutes = Math.floor((safe % 3600) / 60);
  const rest = safe % 60;
  return [hours, minutes, rest].map((part) => String(part).padStart(2, "0")).join(":");
}

async function fetchTaskOptions() {
  const res = await api.get<{ data: TaskOption[] }>("/tasks/options", {
    params: { mias: true },
  });
  return res.data.data ?? [];
}

export function TimeEntriesPage() {
  const user = useAuthStore((state) => state.user);
  const queryClient = useQueryClient();
  const bounds = useMemo(() => weekBounds(), []);
  const [desde, setDesde] = useState(bounds.desde);
  const [hasta, setHasta] = useState(bounds.hasta);
  const [empleado, setEmpleado] = useState("");
  const [page, setPage] = useState(1);
  const [notice, setNotice] = useState("");
  const [error, setError] = useState("");

  const [startOpen, setStartOpen] = useState(false);
  const [startTask, setStartTask] = useState("");
  const [manualOpen, setManualOpen] = useState(false);
  const [editEntry, setEditEntry] = useState<TimeEntry | null>(null);
  const [stopOpen, setStopOpen] = useState(false);

  const isContador = user?.rol === ROLES.CONTADOR;
  const canEditAny = user?.rol === ROLES.DUENO || user?.rol === ROLES.ADMINISTRADOR;

  const [manual, setManual] = useState({
    tarea_id: "",
    fecha: todayISO(),
    horas: "1",
    minutos: "0",
    descripcion: "",
  });
  const [stopDescription, setStopDescription] = useState("");
  const [editForm, setEditForm] = useState({ tarea_id: "", horas: "0", minutos: "30", descripcion: "" });

  const tasksQuery = useQuery({
    queryKey: ["tasks", "options", "time"],
    queryFn: fetchTaskOptions,
    staleTime: 30_000,
  });

  const timerQuery = useQuery({
    queryKey: ["time-entries", "timer"],
    queryFn: async () => {
      const res = await api.get<{ data: TimerState }>("/time-entries/timer");
      return res.data.data;
    },
    refetchInterval: 30_000,
    staleTime: 0,
  });

  const entriesQuery = useQuery({
    queryKey: ["time-entries", "list", { desde, hasta, empleado, page }],
    queryFn: async () => {
      const res = await api.get<{ data: TimeEntry[]; meta: TimeMeta }>("/time-entries", {
        params: {
          fecha_desde: desde || undefined,
          fecha_hasta: hasta || undefined,
          empleado: empleado ? Number(empleado) : undefined,
          page,
        },
      });
      return res.data;
    },
    staleTime: 15_000,
  });

  const timer = timerQuery.data?.activo ?? null;
  const timerId = timer?.id ?? null;
  const [clock, setClock] = useState<{ id: number | null; tick: number }>({ id: null, tick: 0 });

  useEffect(() => {
    if (timerId === null) return;
    const interval = window.setInterval(() => {
      setClock((prev) =>
        prev.id === timerId ? { id: timerId, tick: prev.tick + 1 } : { id: timerId, tick: 1 },
      );
    }, 1000);
    return () => window.clearInterval(interval);
  }, [timerId]);

  const tick = clock.id === timerId ? clock.tick : 0;

  const invalidateTime = () => {
    queryClient.invalidateQueries({ queryKey: ["time-entries"] });
  };

  const startMutation = useMutation({
    mutationFn: async () => {
      await api.post("/time-entries/timer", { tarea_id: Number(startTask) });
    },
    onSuccess: () => {
      setStartOpen(false);
      setStartTask("");
      setNotice("Temporizador iniciado.");
      invalidateTime();
      timerQuery.refetch();
    },
    onError: (err) => setError(getErrorMessage(err)),
  });

  const stopMutation = useMutation({
    mutationFn: async () => {
      const res = await api.post("/time-entries/timer/stop", { descripcion: stopDescription.trim() });
      return res.data.data as { mensaje: string; guardado: boolean; descartado: boolean };
    },
    onSuccess: (data) => {
      setStopOpen(false);
      setStopDescription("");
      setNotice(data.mensaje);
      invalidateTime();
      timerQuery.refetch();
    },
    onError: (err) => setError(getErrorMessage(err)),
  });

  const manualMutation = useMutation({
    mutationFn: async () => {
      await api.post("/time-entries", {
        tarea_id: Number(manual.tarea_id),
        fecha: manual.fecha,
        horas: Number(manual.horas),
        minutos: Number(manual.minutos),
        descripcion: manual.descripcion.trim(),
      });
    },
    onSuccess: () => {
      setManualOpen(false);
      setNotice("Registro manual guardado.");
      setError("");
      invalidateTime();
    },
    onError: (err) => setError(getErrorMessage(err)),
  });

  const editMutation = useMutation({
    mutationFn: async () => {
      if (!editEntry) return;
      await api.put(`/time-entries/${editEntry.id}`, {
        tarea_id: Number(editForm.tarea_id),
        horas: Number(editForm.horas),
        minutos: Number(editForm.minutos),
        descripcion: editForm.descripcion.trim(),
      });
    },
    onSuccess: () => {
      setEditEntry(null);
      setNotice("Registro actualizado.");
      setError("");
      invalidateTime();
    },
    onError: (err) => setError(getErrorMessage(err)),
  });

  const openManual = () => {
    setError("");
    setManual({ tarea_id: "", fecha: todayISO(), horas: "1", minutos: "0", descripcion: "" });
    setManualOpen(true);
  };

  const openEdit = (entry: TimeEntry) => {
    setError("");
    setEditEntry(entry);
    setEditForm({
      tarea_id: String(entry.tarea_id),
      horas: String(Math.floor(entry.duracion_minutos / 60)),
      minutos: String(entry.duracion_minutos % 60),
      descripcion: entry.descripcion,
    });
  };

  const canEdit = (entry: TimeEntry) => canEditAny || (entry.empleado_id === user?.id && entry.fecha === todayISO());

  const items = entriesQuery.data?.data ?? [];
  const meta = entriesQuery.data?.meta;
  const total = meta?.total ?? items.length;

  const elapsed = (timer?.transcurrido_segundos ?? 0) + tick;

  return (
    <div className="mx-auto flex w-full max-w-[1440px] flex-col gap-4">
      <PageHeader
        eyebrow="Módulo 8 · Registro de tiempos"
        title="Registro de Tiempos"
        description="Inicia el temporizador o captura tiempo manualmente. El detalle respeta el alcance por rol."
        actions={
          timer ? (
            <button type="button" className={BTN_SECONDARY} onClick={() => { setStopDescription(""); setStopOpen(true); }}>
              <Square size={15} /> Detener temporizador
            </button>
          ) : (
            <button type="button" className={BTN_PRIMARY} onClick={() => { setStartTask(""); setStartOpen(true); }}>
              <Play size={15} /> Iniciar temporizador
            </button>
          )
        }
      />

      {notice && <Notice tone="success">{notice}</Notice>}
      {error && <Notice tone="danger">{error}</Notice>}

      <section className={`card flex flex-wrap items-center gap-4 p-4 ${timer ? "border-gold-500/40 bg-gold-300/10" : ""}`}>
        <span className={`grid size-11 place-items-center rounded-xl ${timer ? "bg-gold-300 text-navy-900" : "bg-app text-navy-800"}`}>
          <Timer size={21} />
        </span>
        {timer ? (
          <>
            <div className="min-w-0 flex-1">
              <p className="text-[10px] font-semibold uppercase tracking-wide text-gold-700">Temporizador activo</p>
              <p className="truncate text-sm font-semibold text-ink">{timer.tarea_titulo ?? `Tarea ${timer.tarea_id}`}</p>
              <p className="text-xs text-muted">{timer.cliente_nombre ?? "Sin cliente"}</p>
            </div>
            <p className="font-mono text-2xl font-bold tabular-nums text-navy-900">{formatClock(elapsed)}</p>
            <button type="button" className={BTN_PRIMARY} onClick={() => { setStopDescription(""); setStopOpen(true); }}>
              <Square size={15} /> Detener y guardar
            </button>
          </>
        ) : (
          <>
            <div className="min-w-0 flex-1">
              <p className="text-sm font-semibold text-ink">Sin temporizador activo</p>
              <p className="text-xs text-muted">Solo puedes cronometrar tareas asignadas a ti y no completadas.</p>
            </div>
            <button type="button" className={BTN_PRIMARY} onClick={() => { setStartTask(""); setStartOpen(true); }}>
              <Play size={15} /> Iniciar
            </button>
          </>
        )}
      </section>

      <section className="card flex flex-wrap items-end gap-3 p-3">
        <label className="flex flex-col gap-1">
          <span className="text-[10px] font-semibold uppercase tracking-wide text-muted">Desde</span>
          <input type="date" value={desde} max={hasta} onChange={(event) => { setDesde(event.target.value); setPage(1); }} className="rounded-lg border border-line bg-surface px-3 py-2 text-sm text-ink" />
        </label>
        <label className="flex flex-col gap-1">
          <span className="text-[10px] font-semibold uppercase tracking-wide text-muted">Hasta</span>
          <input type="date" value={hasta} min={desde} onChange={(event) => { setHasta(event.target.value); setPage(1); }} className="rounded-lg border border-line bg-surface px-3 py-2 text-sm text-ink" />
        </label>
        {!isContador && (
          <label className="flex min-w-44 flex-col gap-1">
            <span className="text-[10px] font-semibold uppercase tracking-wide text-muted">Empleado</span>
            <input value={empleado} onChange={(event) => { setEmpleado(event.target.value.replace(/\D/g, "")); setPage(1); }} placeholder="Id del colaborador" className="rounded-lg border border-line bg-surface px-3 py-2 text-sm text-ink" />
          </label>
        )}
        <button type="button" className={BTN_SECONDARY} onClick={openManual}>
          <Clock3 size={15} /> Captura manual
        </button>
        <span className="ml-auto text-xs text-muted">
          {meta?.total_horas ?? 0} h en el filtro · {total} registros
        </span>
      </section>

      {entriesQuery.isLoading && <LoadingState label="Cargando registros…" />}
      {entriesQuery.isError && <ErrorState message={getErrorMessage(entriesQuery.error)} />}

      {!entriesQuery.isLoading && !entriesQuery.isError && items.length === 0 && (
        <EmptyState title="Sin registros de tiempo" description="Inicia el temporizador o captura un registro manual." icon={<Timer size={22} />} action={<button type="button" className={BTN_PRIMARY} onClick={openManual}><Clock3 size={15} /> Captura manual</button>} />
      )}

      {items.length > 0 && (
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
                <th className="px-4 py-3 text-right">Acciones</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-line">
              {items.map((entry) => (
                <tr key={entry.id} className="hover:bg-app/50">
                  <td className="px-5 py-3 text-xs text-muted">{formatDate(entry.fecha)}</td>
                  <td className="px-4 py-3 text-xs text-muted">{entry.empleado_nombre ?? entry.empleado_id}</td>
                  <td className="px-4 py-3 text-xs text-muted">{entry.cliente_nombre ?? "—"}</td>
                  <td className="px-4 py-3 text-xs text-muted">{entry.tarea_titulo ?? entry.tarea_id}</td>
                  <td className="px-4 py-3 text-xs text-muted">{entry.tipo === "TIMER" ? "Temporizador" : "Manual"}</td>
                  <td className="px-4 py-3 text-xs font-semibold text-ink">{formatMinutes(entry.duracion_minutos)}</td>
                  <td className="px-4 py-3 text-xs text-muted">{entry.descripcion}</td>
                  <td className="px-4 py-3 text-right">
                    {canEdit(entry) && (
                      <button type="button" className={BTN_GHOST} onClick={() => openEdit(entry)}>
                        <Pencil size={14} /> Editar
                      </button>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          <Pagination page={page} perPage={PER_PAGE} total={total} onChange={setPage} />
        </section>
      )}

      <Modal open={startOpen} onClose={() => setStartOpen(false)} title="Iniciar temporizador" description="Selecciona una tarea asignada a ti.">
        <form
          className="flex flex-col gap-3"
          onSubmit={(event: FormEvent) => { event.preventDefault(); if (startTask) startMutation.mutate(); }}
        >
          <FormField label="Tarea" required>
            <select value={startTask} onChange={(event) => setStartTask(event.target.value)} className={INPUT_CLASS}>
              <option value="">Selecciona una tarea</option>
              {(tasksQuery.data ?? []).map((task) => (
                <option key={task.id} value={task.id}>{task.titulo} · {task.cliente_nombre ?? "Sin cliente"}</option>
              ))}
            </select>
          </FormField>
          {tasksQuery.isLoading && <p className="text-xs text-muted">Cargando tareas…</p>}
          {(tasksQuery.data ?? []).length === 0 && !tasksQuery.isLoading && (
            <p className="rounded-lg bg-amber-50 px-3 py-2 text-xs text-amber-800">No tienes tareas asignadas abiertas.</p>
          )}
          <div className="flex justify-end gap-2">
            <ModalActions onCancel={() => setStartOpen(false)} submitLabel="Iniciar" pending={startMutation.isPending} disabled={!startTask} />
          </div>
        </form>
      </Modal>

      <Modal open={stopOpen} onClose={() => setStopOpen(false)} title="Detener temporizador" description={timer ? `${timer.tarea_titulo ?? "Tarea"} · ${formatClock(elapsed)}` : undefined}>
        <form
          className="flex flex-col gap-3"
          onSubmit={(event) => { event.preventDefault(); stopMutation.mutate(); }}
        >
          <FormField label="Descripción del trabajo" required hint="Entre 5 y 500 caracteres.">
            <textarea value={stopDescription} onChange={(event) => setStopDescription(event.target.value)} rows={3} maxLength={500} className={INPUT_CLASS} />
          </FormField>
          <p className="text-[11px] text-muted">Si el temporizador dura menos de un minuto, el registro se descarta con aviso.</p>
          <div className="flex justify-end gap-2">
            <ModalActions onCancel={() => setStopOpen(false)} submitLabel="Detener y guardar" pending={stopMutation.isPending} disabled={stopDescription.trim().length < 5} />
          </div>
        </form>
      </Modal>

      <Modal open={manualOpen} onClose={() => setManualOpen(false)} title="Captura manual de tiempo" description="Solo se permiten fechas de hoy o anteriores.">
        <form
          className="grid gap-3 sm:grid-cols-2"
          onSubmit={(event) => { event.preventDefault(); manualMutation.mutate(); }}
        >
          <FormField label="Tarea" required className="sm:col-span-2">
            <select value={manual.tarea_id} onChange={(event) => setManual({ ...manual, tarea_id: event.target.value })} className={INPUT_CLASS}>
              <option value="">Selecciona una tarea asignada</option>
              {(tasksQuery.data ?? []).map((task) => (
                <option key={task.id} value={task.id}>{task.titulo} · {task.cliente_nombre ?? "Sin cliente"}</option>
              ))}
            </select>
          </FormField>
          <FormField label="Fecha" required>
            <input type="date" value={manual.fecha} max={todayISO()} onChange={(event) => setManual({ ...manual, fecha: event.target.value })} className={INPUT_CLASS} />
          </FormField>
          <div className="grid grid-cols-2 gap-2">
            <FormField label="Horas" required>
              <input type="number" min={0} max={23} value={manual.horas} onChange={(event) => setManual({ ...manual, horas: event.target.value })} className={INPUT_CLASS} />
            </FormField>
            <FormField label="Minutos" required>
              <input type="number" min={0} max={59} value={manual.minutos} onChange={(event) => setManual({ ...manual, minutos: event.target.value })} className={INPUT_CLASS} />
            </FormField>
          </div>
          <FormField label="Descripción" required className="sm:col-span-2" hint="Entre 5 y 500 caracteres.">
            <textarea value={manual.descripcion} onChange={(event) => setManual({ ...manual, descripcion: event.target.value })} rows={3} maxLength={500} className={INPUT_CLASS} />
          </FormField>
          <div className="flex justify-end gap-2 sm:col-span-2">
            <ModalActions onCancel={() => setManualOpen(false)} submitLabel="Guardar registro" pending={manualMutation.isPending} disabled={!manual.tarea_id || manual.descripcion.trim().length < 5} />
          </div>
        </form>
      </Modal>

      <Modal open={editEntry !== null} onClose={() => setEditEntry(null)} title="Editar registro de tiempo" description={editEntry ? `${formatDate(editEntry.fecha)} · ${editEntry.empleado_nombre ?? ""}` : undefined}>
        <form
          className="grid gap-3 sm:grid-cols-2"
          onSubmit={(event) => { event.preventDefault(); editMutation.mutate(); }}
        >
          <FormField label="Tarea" required className="sm:col-span-2">
            <select value={editForm.tarea_id} onChange={(event) => setEditForm({ ...editForm, tarea_id: event.target.value })} className={INPUT_CLASS}>
              <option value="">Selecciona una tarea</option>
              {(tasksQuery.data ?? []).map((task) => (
                <option key={task.id} value={task.id}>{task.titulo}</option>
              ))}
            </select>
          </FormField>
          <div className="grid grid-cols-2 gap-2 sm:col-span-2">
            <FormField label="Horas">
              <input type="number" min={0} max={23} value={editForm.horas} onChange={(event) => setEditForm({ ...editForm, horas: event.target.value })} className={INPUT_CLASS} />
            </FormField>
            <FormField label="Minutos">
              <input type="number" min={0} max={59} value={editForm.minutos} onChange={(event) => setEditForm({ ...editForm, minutos: event.target.value })} className={INPUT_CLASS} />
            </FormField>
          </div>
          <FormField label="Descripción" required className="sm:col-span-2">
            <textarea value={editForm.descripcion} onChange={(event) => setEditForm({ ...editForm, descripcion: event.target.value })} rows={3} maxLength={500} className={INPUT_CLASS} />
          </FormField>
          <div className="flex justify-end gap-2 sm:col-span-2">
            <ModalActions onCancel={() => setEditEntry(null)} submitLabel="Guardar cambios" pending={editMutation.isPending} disabled={!editForm.tarea_id || editForm.descripcion.trim().length < 5} />
          </div>
        </form>
      </Modal>

      {timerQuery.isLoading && (
        <div className="fixed bottom-4 left-4 flex items-center gap-2 rounded-lg bg-surface px-3 py-2 text-[11px] text-muted shadow-card">
          <Loader2 size={13} className="animate-spin" /> Sincronizando temporizador…
        </div>
      )}
    </div>
  );
}
