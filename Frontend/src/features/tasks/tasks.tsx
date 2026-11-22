import { useMemo, useState, type FormEvent } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Link, useNavigate, useParams, useSearchParams } from "react-router-dom";
import {
  ArrowLeft,
  CalendarDays,
  CheckSquare,
  Clock3,
  History,
  ListChecks,
  Loader2,
  MessageSquare,
  Pencil,
  Plus,
  Send,
  Trash2,
  User,
} from "lucide-react";
import { api } from "@/shared/api/client";
import { ApiError } from "@/shared/api/types";
import { useAuthStore } from "@/shared/auth/authStore";
import { ROLES } from "@/shared/constants/roles";
import {
  ESTADO_BADGE,
  ESTADO_LABELS,
  ESTADOS_TAREA,
  INPUT_CLASS,
  PRIORIDAD_BADGE,
  PRIORIDAD_LABELS,
  PRIORIDADES,
  SEMAFORO_BADGE,
  SEMAFORO_LABELS,
  BTN_DANGER,
  BTN_GHOST,
  BTN_PRIMARY,
  BTN_SECONDARY,
} from "@/shared/constants/constants";
import {
  Badge,
  EmptyState,
  ErrorState,
  FormField,
  LoadingState,
  Modal,
  ModalActions,
  PageHeader,
  ProgressBar,
} from "@/shared/components/components";
import { Pagination } from "@/shared/components/Pagination";
import {
  formatDate,
  formatDateTime,
  formatHours,
  getErrorMessage,
  todayISO,
} from "@/shared/utils/utils";

const PER_PAGE = 20;

interface ClienteOption {
  id: number;
  nombre_completo: string;
  rfc: string;
  estatus: string;
}

interface UserOption {
  id: number;
  nombre_completo: string;
  rol: string;
}

interface Subcategoria {
  id: number;
  nombre: string;
  activa: boolean;
}

interface Categoria {
  id: number;
  nombre: string;
  activa: boolean;
  subcategorias?: Subcategoria[];
}

interface TareaItem {
  id: number;
  titulo: string;
  cliente_id: number;
  cliente_nombre: string | null;
  categoria_id: number;
  categoria_nombre: string | null;
  categoria_padre_nombre: string | null;
  asignado_id: number;
  asignado_nombre: string | null;
  prioridad: string;
  estado: string;
  fecha_limite: string;
  hora_limite: string | null;
  semaforo: string;
  dias_restantes: number;
}

interface Subtarea {
  id: number;
  titulo: string;
  completada: boolean;
  completada_por: number | null;
  completada_por_nombre: string | null;
  completada_en: string | null;
  created_at: string;
}

interface Comentario {
  id: number;
  autor_id: number;
  autor_nombre: string | null;
  texto: string;
  editado: boolean;
  created_at: string;
  updated_at: string;
}

interface Historial {
  id: number;
  estado_anterior: string | null;
  estado_nuevo: string;
  usuario_nombre: string | null;
  created_at: string;
}

interface TareaDetail extends TareaItem {
  descripcion: string | null;
  creador_id: number | null;
  creador_nombre: string | null;
  horas_estimadas: number | null;
  notificar_cliente: boolean;
  completada_en: string | null;
  completada_por_nombre: string | null;
  created_at: string;
  subtareas: {
    items: Subtarea[];
    total: number;
    completadas: number;
    avance: string;
    porcentaje: number;
  };
  comentarios: Comentario[];
  historial_estados: Historial[];
  tiempo: {
    total_minutos: number;
    total_horas: number;
    horas_estimadas: number | null;
    porcentaje_registrado: number | null;
    por_colaborador: Array<{ colaborador_id: number; colaborador_nombre: string; minutos: number; horas: number }>;
  };
}

interface OptionsResponse<T> {
  data: T[];
}

async function fetchTasks(params: Record<string, string | number | undefined>) {
  const res = await api.get<{ data: TareaItem[]; meta?: { page: number; per_page: number; total: number } }>(
    "/tasks",
    { params },
  );
  return res.data;
}

async function fetchTaskOptions<T>(url: string) {
  const res = await api.get<OptionsResponse<T>>(url);
  return res.data.data ?? [];
}

function flattenCategories(categories: Categoria[]) {
  const rows: Array<{ id: number; label: string; activa: boolean }> = [];
  for (const category of categories) {
    rows.push({ id: category.id, label: category.nombre, activa: category.activa });
    for (const sub of category.subcategorias ?? []) {
      rows.push({
        id: sub.id,
        label: `${category.nombre} / ${sub.nombre}`,
        activa: sub.activa,
      });
    }
  }
  return rows;
}

// ---------------------------------------------------------------------------
// Formulario de alta / edición
// ---------------------------------------------------------------------------
function TaskForm({
  task,
  clients,
  users,
  categories,
  onCancel,
  onSaved,
}: {
  task: TareaDetail | null;
  clients: ClienteOption[];
  users: UserOption[];
  categories: Categoria[];
  onCancel: () => void;
  onSaved: () => void;
}) {
  const [titulo, setTitulo] = useState(task?.titulo ?? "");
  const [descripcion, setDescripcion] = useState(task?.descripcion ?? "");
  const [clienteId, setClienteId] = useState(String(task?.cliente_id ?? ""));
  const [categoriaId, setCategoriaId] = useState(String(task?.categoria_id ?? ""));
  const [asignadoId, setAsignadoId] = useState(String(task?.asignado_id ?? ""));
  const [fecha, setFecha] = useState(task?.fecha_limite ?? todayISO());
  const [hora, setHora] = useState(task?.hora_limite ?? "23:59");
  const [prioridad, setPrioridad] = useState(task?.prioridad ?? "MEDIA");
  const [horas, setHoras] = useState(task?.horas_estimadas ? String(task.horas_estimadas) : "");
  const [notificar, setNotificar] = useState(task?.notificar_cliente ?? true);
  const [error, setError] = useState("");

  const categorias = useMemo(() => flattenCategories(categories), [categories]);
  const contadores = users.filter((user) => user.rol === ROLES.CONTADOR);

  const mutation = useMutation({
    mutationFn: async () => {
      const payload = {
        titulo: titulo.trim(),
        descripcion: descripcion.trim() || null,
        cliente_id: Number(clienteId),
        categoria_id: Number(categoriaId),
        asignado_id: Number(asignadoId),
        fecha_limite: fecha,
        hora_limite: hora || "23:59",
        prioridad,
        horas_estimadas: horas ? Number(horas) : null,
        notificar_cliente: notificar,
      };
      if (task) {
        const res = await api.put(`/tasks/${task.id}`, payload);
        return res.data;
      }
      const res = await api.post("/tasks", payload);
      return res.data;
    },
    onSuccess: onSaved,
    onError: (err) => setError(getErrorMessage(err)),
  });

  const submit = (event: FormEvent) => {
    event.preventDefault();
    setError("");
    if (titulo.trim().length < 5) {
      setError("El título debe tener al menos 5 caracteres.");
      return;
    }
    if (!clienteId || !categoriaId || !asignadoId || !fecha) {
      setError("Completa cliente, categoría, responsable y fecha límite.");
      return;
    }
    mutation.mutate();
  };

  return (
    <form id="task-form" onSubmit={submit} className="grid gap-3 sm:grid-cols-2">
      {error && <p className="sm:col-span-2 rounded-lg bg-rose-50 px-3 py-2 text-xs font-medium text-rose-700">{error}</p>}
      <FormField label="Título" required className="sm:col-span-2">
        <input
          value={titulo}
          onChange={(event) => setTitulo(event.target.value)}
          maxLength={100}
          placeholder="Ej. Declaración mensual de IVA"
          className={INPUT_CLASS}
        />
      </FormField>
      <FormField label="Descripción" className="sm:col-span-2">
        <textarea
          value={descripcion}
          onChange={(event) => setDescripcion(event.target.value)}
          rows={3}
          maxLength={2000}
          className={INPUT_CLASS}
        />
      </FormField>
      <FormField label="Cliente" required>
        <select value={clienteId} onChange={(event) => setClienteId(event.target.value)} className={INPUT_CLASS}>
          <option value="">Selecciona un cliente</option>
          {clients.map((cliente) => (
            <option key={cliente.id} value={cliente.id}>
              {cliente.nombre_completo} {cliente.estatus !== "ACTIVO" ? `(${cliente.estatus})` : ""}
            </option>
          ))}
        </select>
      </FormField>
      <FormField label="Categoría" required>
        <select value={categoriaId} onChange={(event) => setCategoriaId(event.target.value)} className={INPUT_CLASS}>
          <option value="">Selecciona una categoría</option>
          {categorias.filter((category) => category.activa).map((category) => (
            <option key={category.id} value={category.id}>
              {category.label}
            </option>
          ))}
        </select>
      </FormField>
      <FormField label="Responsable (Contador)" required>
        <select value={asignadoId} onChange={(event) => setAsignadoId(event.target.value)} className={INPUT_CLASS}>
          <option value="">Selecciona un contador</option>
          {contadores.map((user) => (
            <option key={user.id} value={user.id}>
              {user.nombre_completo}
            </option>
          ))}
        </select>
      </FormField>
      <FormField label="Prioridad" required>
        <select value={prioridad} onChange={(event) => setPrioridad(event.target.value)} className={INPUT_CLASS}>
          {PRIORIDADES.map((item) => (
            <option key={item} value={item}>
              {PRIORIDAD_LABELS[item]}
            </option>
          ))}
        </select>
      </FormField>
      <FormField label="Fecha límite" required>
        <input type="date" value={fecha} min={task ? undefined : todayISO()} onChange={(event) => setFecha(event.target.value)} className={INPUT_CLASS} />
      </FormField>
      <FormField label="Hora límite">
        <input type="time" value={hora} onChange={(event) => setHora(event.target.value)} className={INPUT_CLASS} />
      </FormField>
      <FormField label="Horas estimadas" hint="Múltiplos de 0.5">
        <input
          type="number"
          min={0.5}
          max={200}
          step={0.5}
          value={horas}
          onChange={(event) => setHoras(event.target.value)}
          className={INPUT_CLASS}
        />
      </FormField>
      <label className="mt-6 flex items-center gap-2 text-sm text-ink">
        <input type="checkbox" checked={notificar} onChange={(event) => setNotificar(event.target.checked)} className="size-4 rounded border-line accent-navy-900" />
        Notificar al cliente por correo
      </label>
      <div className="sm:col-span-2 flex justify-end gap-2">
        <ModalActions onCancel={onCancel} submitLabel={task ? "Guardar cambios" : "Crear tarea"} pending={mutation.isPending} formId="task-form" />
      </div>
    </form>
  );
}

// ---------------------------------------------------------------------------
// Listado
// ---------------------------------------------------------------------------
export function TasksPage() {
  const user = useAuthStore((state) => state.user);
  const queryClient = useQueryClient();
  const [searchParams] = useSearchParams();
  const [page, setPage] = useState(1);
  const [estado, setEstado] = useState("");
  const [prioridad, setPrioridad] = useState("");
  const [cliente, setCliente] = useState(() => searchParams.get("cliente") ?? "");
  const [responsable, setResponsable] = useState("");
  const [editorOpen, setEditorOpen] = useState(false);
  const [editId, setEditId] = useState<number | null>(null);

  const canCreate = ["DUENO", "ADMINISTRADOR", "COORDINADOR"].includes(user?.rol ?? "");

  const params = useMemo(
    () => ({
      page,
      estado: estado || undefined,
      prioridad: prioridad || undefined,
      cliente: cliente ? Number(cliente) : undefined,
      responsable: responsable ? Number(responsable) : undefined,
    }),
    [page, estado, prioridad, cliente, responsable],
  );

  const listQuery = useQuery({
    queryKey: ["tasks", "list", params],
    queryFn: () => fetchTasks(params),
    staleTime: 15_000,
  });

  const clientsQuery = useQuery({
    queryKey: ["clients", "options", "tasks"],
    queryFn: () => fetchTaskOptions<ClienteOption>("/clients/options"),
    staleTime: 60_000,
  });
  const usersQuery = useQuery({
    queryKey: ["users", "options", "tasks"],
    queryFn: () => fetchTaskOptions<UserOption>("/users/options"),
    staleTime: 60_000,
  });
  const catalogQuery = useQuery({
    queryKey: ["catalog", "options", "tasks"],
    queryFn: async () => {
      const res = await api.get<{ data: Categoria[] }>("/catalog", {
        params: { solo_activas: true },
      });
      return res.data.data ?? [];
    },
    staleTime: 60_000,
  });

  const detailQuery = useQuery({
    queryKey: ["tasks", "detail", editId],
    queryFn: async () => {
      const res = await api.get<{ data: TareaDetail }>(`/tasks/${editId}`);
      return res.data.data;
    },
    enabled: editorOpen && editId !== null,
    retry: false,
  });

  const deleteMutation = useMutation({
    mutationFn: async (id: number) => {
      await api.delete(`/tasks/${id}`);
    },
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["tasks"] }),
    onError: (err) => window.alert(getErrorMessage(err)),
  });

  const openCreate = () => {
    setEditId(null);
    setEditorOpen(true);
  };

  const openEdit = (id: number) => {
    setEditId(id);
    setEditorOpen(true);
  };

  const closeEditor = () => {
    setEditorOpen(false);
    setEditId(null);
  };

  const items = listQuery.data?.data ?? [];
  const meta = listQuery.data?.meta;
  const total = meta?.total ?? items.length;

  return (
    <div className="mx-auto flex w-full max-w-[1440px] flex-col gap-4">
      <PageHeader
        eyebrow="Módulo 5 · Tareas, subtareas y comentarios"
        title="Listado de Tareas"
        description="Consulta, crea y da seguimiento a las tareas del despacho."
        actions={
          canCreate && (
            <button type="button" className={BTN_PRIMARY} onClick={openCreate}>
              <Plus size={16} /> Nueva tarea
            </button>
          )
        }
      />

      <section className="card flex flex-wrap items-center gap-3 p-3">
        <select value={estado} onChange={(event) => { setEstado(event.target.value); setPage(1); }} className="rounded-lg border border-line bg-surface px-3 py-2 text-sm text-ink">
          <option value="">Todos los estados</option>
          {ESTADOS_TAREA.map((item) => (
            <option key={item} value={item}>{ESTADO_LABELS[item]}</option>
          ))}
        </select>
        <select value={prioridad} onChange={(event) => { setPrioridad(event.target.value); setPage(1); }} className="rounded-lg border border-line bg-surface px-3 py-2 text-sm text-ink">
          <option value="">Todas las prioridades</option>
          {PRIORIDADES.map((item) => (
            <option key={item} value={item}>{PRIORIDAD_LABELS[item]}</option>
          ))}
        </select>
        <select value={cliente} onChange={(event) => { setCliente(event.target.value); setPage(1); }} className="rounded-lg border border-line bg-surface px-3 py-2 text-sm text-ink">
          <option value="">Todos los clientes</option>
          {(clientsQuery.data ?? []).map((option) => (
            <option key={option.id} value={option.id}>{option.nombre_completo}</option>
          ))}
        </select>
        <select value={responsable} onChange={(event) => { setResponsable(event.target.value); setPage(1); }} className="rounded-lg border border-line bg-surface px-3 py-2 text-sm text-ink">
          <option value="">Todos los responsables</option>
          {(usersQuery.data ?? []).map((option) => (
            <option key={option.id} value={option.id}>{option.nombre_completo}</option>
          ))}
        </select>
        <span className="ml-auto text-xs text-muted">{total} tareas</span>
      </section>

      {listQuery.isLoading && <LoadingState label="Cargando tareas…" />}
      {listQuery.isError && <ErrorState message={getErrorMessage(listQuery.error)} />}

      {!listQuery.isLoading && !listQuery.isError && items.length === 0 && (
        <EmptyState
          title="Sin tareas para los filtros seleccionados"
          description="Ajusta los filtros o crea una tarea nueva."
          icon={<ListChecks size={22} />}
          action={canCreate ? <button type="button" className={BTN_PRIMARY} onClick={openCreate}><Plus size={16} /> Nueva tarea</button> : undefined}
        />
      )}

      {items.length > 0 && (
        <section className="card overflow-x-auto">
          <table className="w-full text-left">
            <thead className="border-b border-line bg-app/60">
              <tr className="text-[10px] font-semibold uppercase tracking-[0.1em] text-muted">
                <th className="px-5 py-3">Tarea</th>
                <th className="px-4 py-3">Cliente</th>
                <th className="px-4 py-3">Responsable</th>
                <th className="px-4 py-3">Prioridad</th>
                <th className="px-4 py-3">Estado</th>
                <th className="px-4 py-3">Fecha límite</th>
                <th className="px-4 py-3">Semáforo</th>
                <th className="px-4 py-3 text-right">Acciones</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-line">
              {items.map((task) => (
                <tr key={task.id} className="hover:bg-app/50">
                  <td className="px-5 py-3">
                    <Link to={`/tareas/${task.id}`} className="text-sm font-semibold text-ink hover:text-navy-800">
                      {task.titulo}
                    </Link>
                    <p className="text-[11px] text-muted">
                      {task.categoria_padre_nombre ? `${task.categoria_padre_nombre} / ` : ""}
                      {task.categoria_nombre ?? "Sin categoría"}
                    </p>
                  </td>
                  <td className="px-4 py-3 text-xs text-muted">{task.cliente_nombre ?? task.cliente_id}</td>
                  <td className="px-4 py-3 text-xs text-muted">{task.asignado_nombre ?? task.asignado_id}</td>
                  <td className="px-4 py-3">
                    <Badge className={PRIORIDAD_BADGE[task.prioridad]}>{PRIORIDAD_LABELS[task.prioridad] ?? task.prioridad}</Badge>
                  </td>
                  <td className="px-4 py-3">
                    <Badge className={ESTADO_BADGE[task.estado]}>{ESTADO_LABELS[task.estado] ?? task.estado}</Badge>
                  </td>
                  <td className="px-4 py-3 text-xs text-muted">
                    {formatDate(task.fecha_limite)}{task.hora_limite ? ` · ${task.hora_limite}` : ""}
                  </td>
                  <td className="px-4 py-3">
                    <Badge className={SEMAFORO_BADGE[task.semaforo]}>{SEMAFORO_LABELS[task.semaforo] ?? task.semaforo}</Badge>
                  </td>
                  <td className="px-4 py-3">
                    <div className="flex items-center justify-end gap-1">
                      <Link to={`/tareas/${task.id}`} className={BTN_GHOST} title="Ver detalle">
                        <ListChecks size={14} />
                      </Link>
                      <button type="button" className={BTN_GHOST} onClick={() => openEdit(task.id)} title="Editar">
                        <Pencil size={14} />
                      </button>
                      <button
                        type="button"
                        className={BTN_DANGER}
                        title="Eliminar"
                        onClick={() => {
                          if (window.confirm(`¿Eliminar la tarea "${task.titulo}"?`)) {
                            deleteMutation.mutate(task.id);
                          }
                        }}
                      >
                        <Trash2 size={14} />
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          <Pagination page={page} perPage={PER_PAGE} total={total} onChange={setPage} />
        </section>
      )}

      <Modal
        open={editorOpen}
        onClose={closeEditor}
        title={editId ? "Editar tarea" : "Nueva tarea"}
        description={editId ? "Actualiza los datos de la tarea." : "Completa los datos para registrar una tarea."}
        wide
      >
        {editId && detailQuery.isLoading ? (
          <LoadingState label="Cargando tarea…" />
        ) : editId && detailQuery.isError ? (
          <ErrorState message={getErrorMessage(detailQuery.error)} />
        ) : (
          <TaskForm
            key={editId ?? "nueva"}
            task={editId ? detailQuery.data ?? null : null}
            clients={clientsQuery.data ?? []}
            users={usersQuery.data ?? []}
            categories={catalogQuery.data ?? []}
            onCancel={closeEditor}
            onSaved={() => {
              queryClient.invalidateQueries({ queryKey: ["tasks"] });
              closeEditor();
            }}
          />
        )}
      </Modal>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Detalle de tarea
// ---------------------------------------------------------------------------
export function TaskDetailPage() {
  const { id } = useParams();
  const taskId = Number(id);
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const user = useAuthStore((state) => state.user);
  const [subtaskTitle, setSubtaskTitle] = useState("");
  const [commentText, setCommentText] = useState("");
  const [editingComment, setEditingComment] = useState<number | null>(null);
  const [editingText, setEditingText] = useState("");
  const [actionError, setActionError] = useState("");

  const detailQuery = useQuery({
    queryKey: ["tasks", "detail", taskId],
    queryFn: async () => {
      const res = await api.get<{ data: TareaDetail }>(`/tasks/${taskId}`);
      return res.data.data;
    },
    enabled: Number.isInteger(taskId) && taskId > 0,
    retry: false,
  });

  const task = detailQuery.data;
  const refresh = () => queryClient.invalidateQueries({ queryKey: ["tasks"] });

  const subtaskMutation = useMutation({
    mutationFn: async ({ action, subtareaId, title }: { action: "add" | "toggle" | "delete"; subtareaId?: number; title?: string }) => {
      if (action === "add") {
        await api.post(`/tasks/${taskId}/subtasks`, { titulo: title });
      } else if (action === "toggle") {
        const current = task?.subtareas.items.find((item) => item.id === subtareaId);
        await api.put(`/tasks/${taskId}/subtasks/${subtareaId}`, { completada: !current?.completada });
      } else {
        await api.delete(`/tasks/${taskId}/subtasks/${subtareaId}`);
      }
    },
    onSuccess: () => {
      setSubtaskTitle("");
      setActionError("");
      refresh();
      queryClient.invalidateQueries({ queryKey: ["tasks", "detail", taskId] });
    },
    onError: (err) => setActionError(getErrorMessage(err)),
  });

  const commentMutation = useMutation({
    mutationFn: async ({ action, comentarioId, texto }: { action: "add" | "edit" | "delete"; comentarioId?: number; texto?: string }) => {
      if (action === "add") {
        await api.post(`/tasks/${taskId}/comments`, { texto });
      } else if (action === "edit") {
        await api.put(`/tasks/${taskId}/comments/${comentarioId}`, { texto });
      } else {
        await api.delete(`/tasks/${taskId}/comments/${comentarioId}`);
      }
    },
    onSuccess: () => {
      setCommentText("");
      setEditingComment(null);
      setEditingText("");
      setActionError("");
      queryClient.invalidateQueries({ queryKey: ["tasks", "detail", taskId] });
    },
    onError: (err) => setActionError(getErrorMessage(err)),
  });

  // El estado destino de un movimiento pendiente de confirmación (RG-14).
  const [pendingMove, setPendingMove] = useState("POR_HACER");

  const moveMutation = useMutation({
    mutationFn: async ({ estado, confirmar }: { estado: string; confirmar: boolean }) => {
      await api.patch(`/tasks/${taskId}/estado`, {
        estado,
        confirmar_subtareas_pendientes: confirmar,
      });
    },
    onSuccess: () => {
      setActionError("");
      refresh();
      queryClient.invalidateQueries({ queryKey: ["tasks", "detail", taskId] });
    },
    onError: (err) => {
      if (err instanceof ApiError && err.status === 409) {
        if (window.confirm(`${err.message}\n\n¿Deseas moverla de todos modos?`)) {
          moveMutation.mutate({ estado: pendingMove, confirmar: true });
        }
        return;
      }
      setActionError(getErrorMessage(err));
    },
  });

  const deleteMutation = useMutation({
    mutationFn: async () => {
      await api.delete(`/tasks/${taskId}`);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["tasks"] });
      navigate("/tareas");
    },
    onError: (err) => setActionError(getErrorMessage(err)),
  });

  if (detailQuery.isLoading) return <LoadingState label="Cargando tarea…" />;
  if (detailQuery.isError) return <ErrorState message={getErrorMessage(detailQuery.error)} />;
  if (!task) return <ErrorState message="Tarea no encontrada." />;

  const canModerate = user?.rol === ROLES.DUENO || user?.rol === ROLES.ADMINISTRADOR;

  return (
    <div className="mx-auto flex w-full max-w-[1240px] flex-col gap-4">
      <Link to="/tareas" className="inline-flex w-fit items-center gap-1.5 text-xs font-semibold text-muted hover:text-ink">
        <ArrowLeft size={14} /> Volver al listado
      </Link>

      <header className="card p-5">
        <div className="flex flex-wrap items-start justify-between gap-4">
          <div>
            <div className="flex flex-wrap items-center gap-2">
              <Badge className={ESTADO_BADGE[task.estado]}>{ESTADO_LABELS[task.estado] ?? task.estado}</Badge>
              <Badge className={PRIORIDAD_BADGE[task.prioridad]}>{PRIORIDAD_LABELS[task.prioridad] ?? task.prioridad}</Badge>
              <Badge className={SEMAFORO_BADGE[task.semaforo]}>{SEMAFORO_LABELS[task.semaforo] ?? task.semaforo}</Badge>
            </div>
            <h1 className="mt-2 font-display text-2xl font-bold text-ink">{task.titulo}</h1>
            <p className="mt-1 text-sm text-muted">
              {task.cliente_nombre ?? "Cliente"} · {task.categoria_padre_nombre ? `${task.categoria_padre_nombre} / ` : ""}
              {task.categoria_nombre ?? "Sin categoría"}
            </p>
          </div>
          <div className="flex flex-wrap items-center gap-2">
            <select
              value={task.estado}
              onChange={(event) => {
                setPendingMove(event.target.value);
                moveMutation.mutate({ estado: event.target.value, confirmar: false });
              }}
              className="rounded-lg border border-line bg-surface px-3 py-2 text-xs font-semibold text-ink"
              disabled={moveMutation.isPending}
            >
              {ESTADOS_TAREA.map((item) => (
                <option key={item} value={item}>{ESTADO_LABELS[item]}</option>
              ))}
            </select>
            <button
              type="button"
              className={BTN_DANGER}
              onClick={() => {
                if (window.confirm(`¿Eliminar la tarea "${task.titulo}"?`)) deleteMutation.mutate();
              }}
            >
              <Trash2 size={14} /> Eliminar
            </button>
          </div>
        </div>
        {actionError && <p className="mt-3 rounded-lg bg-rose-50 px-3 py-2 text-xs font-medium text-rose-700">{actionError}</p>}
      </header>

      <section className="grid gap-3 md:grid-cols-2 xl:grid-cols-4">
        <div className="card p-4">
          <p className="text-[10px] uppercase tracking-wide text-muted">Responsable</p>
          <p className="mt-1 flex items-center gap-1.5 text-sm font-semibold text-ink"><User size={14} /> {task.asignado_nombre ?? "—"}</p>
        </div>
        <div className="card p-4">
          <p className="text-[10px] uppercase tracking-wide text-muted">Fecha límite</p>
          <p className="mt-1 flex items-center gap-1.5 text-sm font-semibold text-ink"><CalendarDays size={14} /> {formatDate(task.fecha_limite)} {task.hora_limite}</p>
        </div>
        <div className="card p-4">
          <p className="text-[10px] uppercase tracking-wide text-muted">Tiempo registrado</p>
          <p className="mt-1 flex items-center gap-1.5 text-sm font-semibold text-ink"><Clock3 size={14} /> {formatHours(task.tiempo.total_minutos)}</p>
          <p className="mt-1 text-[11px] text-muted">{task.horas_estimadas ? `Estimadas: ${task.horas_estimadas} h` : "Sin estimación"}</p>
        </div>
        <div className="card p-4">
          <p className="text-[10px] uppercase tracking-wide text-muted">Creada por</p>
          <p className="mt-1 text-sm font-semibold text-ink">{task.creador_nombre ?? "—"}</p>
          <p className="mt-1 text-[11px] text-muted">{formatDateTime(task.created_at)}</p>
        </div>
      </section>

      {task.descripcion && (
        <section className="card p-4">
          <h2 className="text-sm font-semibold text-ink">Descripción</h2>
          <p className="mt-2 whitespace-pre-wrap text-sm text-muted">{task.descripcion}</p>
        </section>
      )}

      <section className="grid gap-3 xl:grid-cols-2">
        <div className="card p-4">
          <header className="flex items-center justify-between gap-2">
            <h2 className="flex items-center gap-1.5 text-sm font-semibold text-ink"><CheckSquare size={16} /> Subtareas</h2>
            <span className="text-xs text-muted">{task.subtareas.completadas}/{task.subtareas.total}</span>
          </header>
          <ProgressBar value={task.subtareas.porcentaje} className="mt-3" />
          <p className="mt-1 text-[11px] text-muted">{task.subtareas.avance}</p>

          <ul className="mt-3 flex flex-col gap-1.5">
            {task.subtareas.items.map((subtask) => (
              <li key={subtask.id} className="flex items-center gap-2 rounded-lg border border-line px-3 py-2">
                <input
                  type="checkbox"
                  checked={subtask.completada}
                  onChange={() => subtaskMutation.mutate({ action: "toggle", subtareaId: subtask.id })}
                  className="size-4 rounded border-line accent-navy-900"
                />
                <span className={`flex-1 text-xs ${subtask.completada ? "text-muted line-through" : "text-ink"}`}>{subtask.titulo}</span>
                <button type="button" className={BTN_GHOST} onClick={() => subtaskMutation.mutate({ action: "delete", subtareaId: subtask.id })} title="Eliminar subtarea">
                  <Trash2 size={13} />
                </button>
              </li>
            ))}
            {task.subtareas.items.length === 0 && <li className="py-2 text-center text-xs text-muted">Sin subtareas.</li>}
          </ul>

          <form
            className="mt-3 flex gap-2"
            onSubmit={(event) => {
              event.preventDefault();
              if (subtaskTitle.trim()) subtaskMutation.mutate({ action: "add", title: subtaskTitle.trim() });
            }}
          >
            <input
              value={subtaskTitle}
              onChange={(event) => setSubtaskTitle(event.target.value)}
              placeholder="Nuevo paso verificable…"
              maxLength={150}
              className={INPUT_CLASS}
            />
            <button type="submit" className={BTN_SECONDARY} disabled={subtaskMutation.isPending || !subtaskTitle.trim()}>
              <Plus size={14} />
            </button>
          </form>
        </div>

        <div className="card p-4">
          <h2 className="flex items-center gap-1.5 text-sm font-semibold text-ink"><MessageSquare size={16} /> Comentarios</h2>
          <form
            className="mt-3 flex flex-col gap-2"
            onSubmit={(event) => {
              event.preventDefault();
              if (commentText.trim()) commentMutation.mutate({ action: "add", texto: commentText.trim() });
            }}
          >
            <textarea
              value={commentText}
              onChange={(event) => setCommentText(event.target.value)}
              rows={3}
              maxLength={1000}
              placeholder="Escribe un comentario…"
              className={INPUT_CLASS}
            />
            <button type="submit" className={`${BTN_SECONDARY} self-end`} disabled={commentMutation.isPending || !commentText.trim()}>
              <Send size={14} /> Publicar
            </button>
          </form>

          <ul className="mt-4 flex flex-col gap-3">
            {task.comentarios.map((comment) => {
              const canEdit = comment.autor_id === user?.id || canModerate;
              return (
                <li key={comment.id} className="rounded-lg border border-line bg-app/30 p-3">
                  <div className="flex items-center justify-between gap-2">
                    <p className="text-xs font-semibold text-ink">{comment.autor_nombre ?? "Usuario"}</p>
                    <span className="text-[10px] text-muted">{formatDateTime(comment.created_at)}{comment.editado ? " · editado" : ""}</span>
                  </div>
                  {editingComment === comment.id ? (
                    <div className="mt-2 flex flex-col gap-2">
                      <textarea value={editingText} onChange={(event) => setEditingText(event.target.value)} rows={2} maxLength={1000} className={INPUT_CLASS} />
                      <div className="flex justify-end gap-2">
                        <button type="button" className={BTN_GHOST} onClick={() => setEditingComment(null)}>Cancelar</button>
                        <button type="button" className={BTN_SECONDARY} onClick={() => commentMutation.mutate({ action: "edit", comentarioId: comment.id, texto: editingText.trim() })} disabled={!editingText.trim()}>Guardar</button>
                      </div>
                    </div>
                  ) : (
                    <>
                      <p className="mt-1 whitespace-pre-wrap text-xs text-muted">{comment.texto}</p>
                      {canEdit && (
                        <div className="mt-2 flex justify-end gap-1">
                          <button type="button" className={BTN_GHOST} onClick={() => { setEditingComment(comment.id); setEditingText(comment.texto); }}>Editar</button>
                          <button type="button" className={BTN_GHOST} onClick={() => { if (window.confirm("¿Eliminar este comentario?")) commentMutation.mutate({ action: "delete", comentarioId: comment.id }); }}>Eliminar</button>
                        </div>
                      )}
                    </>
                  )}
                </li>
              );
            })}
            {task.comentarios.length === 0 && <li className="py-3 text-center text-xs text-muted">Sin comentarios todavía.</li>}
          </ul>
        </div>
      </section>

      <section className="grid gap-3 xl:grid-cols-2">
        <div className="card p-4">
          <h2 className="flex items-center gap-1.5 text-sm font-semibold text-ink"><History size={16} /> Historial de estados</h2>
          <ul className="mt-3 flex flex-col gap-2">
            {task.historial_estados.map((item) => (
              <li key={item.id} className="flex items-center justify-between gap-2 text-xs">
                <span className="text-muted">
                  {item.estado_anterior ? `${ESTADO_LABELS[item.estado_anterior] ?? item.estado_anterior} → ` : ""}
                  <span className="font-semibold text-ink">{ESTADO_LABELS[item.estado_nuevo] ?? item.estado_nuevo}</span>
                  {item.usuario_nombre ? ` · ${item.usuario_nombre}` : ""}
                </span>
                <span className="shrink-0 text-[10px] text-muted">{formatDateTime(item.created_at)}</span>
              </li>
            ))}
            {task.historial_estados.length === 0 && <li className="py-3 text-center text-xs text-muted">Sin movimientos registrados.</li>}
          </ul>
        </div>

        <div className="card p-4">
          <h2 className="text-sm font-semibold text-ink">Tiempo por colaborador</h2>
          <ul className="mt-3 flex flex-col gap-2">
            {task.tiempo.por_colaborador.map((row) => (
              <li key={row.colaborador_id} className="flex items-center justify-between text-xs">
                <span className="text-muted">{row.colaborador_nombre}</span>
                <span className="font-semibold text-ink">{formatHours(row.minutos)}</span>
              </li>
            ))}
            {task.tiempo.por_colaborador.length === 0 && <li className="py-3 text-center text-xs text-muted">Sin tiempo registrado.</li>}
          </ul>
        </div>
      </section>

      {moveMutation.isPending && (
        <div className="fixed bottom-4 right-4 flex items-center gap-2 rounded-lg bg-navy-900 px-4 py-2 text-xs font-semibold text-white shadow-lg">
          <Loader2 size={14} className="animate-spin" /> Actualizando estado…
        </div>
      )}
    </div>
  );
}
