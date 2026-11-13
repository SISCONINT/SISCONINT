import { useMemo, useState, type FormEvent } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useSearchParams } from "react-router-dom";
import { Download, Eye, FileText, Pencil, Plus, Trash2 } from "lucide-react";
import { api } from "@/shared/api/client";
import { useAuthStore } from "@/shared/auth/authStore";
import { ROLES } from "@/shared/constants/roles";
import {
  BTN_DANGER,
  BTN_GHOST,
  BTN_PRIMARY,
  BTN_SECONDARY,
  INPUT_CLASS,
  TIPOS_MINUTA,
  TIPO_MINUTA_LABELS,
} from "@/shared/constants/constants";
import {
  Badge,
  EmptyState,
  ErrorState,
  FormField,
  LoadingState,
  Modal,
  Notice,
  PageHeader,
} from "@/shared/components/components";
import { Pagination } from "@/shared/components/Pagination";
import { formatDate, getErrorMessage, todayISO } from "@/shared/utils/utils";

const PER_PAGE = 20;
const MAX_BYTES = 10 * 1024 * 1024;
const MIME_PERMITIDOS = [
  "application/pdf",
  "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
  "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
  "image/jpeg",
  "image/png",
];
const EXTENSIONES = ".pdf,.docx,.xlsx,.jpg,.jpeg,.png";

interface ClienteOption {
  id: number;
  nombre_completo: string;
}

interface TaskOption {
  id: number;
  titulo: string;
  cliente_id: number;
  cliente_nombre: string | null;
  estado: string;
  fecha_limite: string;
}

interface Minuta {
  id: number;
  tipo: string;
  titulo: string;
  fecha_reunion: string;
  cliente_id: number | null;
  cliente_nombre: string | null;
  tarea_id: number | null;
  tarea_titulo: string | null;
  observaciones: string | null;
  cargada_por: number;
  cargador_nombre: string | null;
  archivo_nombre: string;
  archivo_mime: string;
  archivo_bytes: number;
  created_at: string;
}

interface ListResponse {
  data: Minuta[];
  meta?: { page: number; per_page: number; total: number; pages?: number };
}

interface FormState {
  tipo: string;
  cliente_id: string;
  tarea_id: string;
  titulo: string;
  fecha_reunion: string;
  observaciones: string;
}

const EMPTY_FORM: FormState = {
  tipo: "CLIENTE",
  cliente_id: "",
  tarea_id: "",
  titulo: "",
  fecha_reunion: todayISO(),
  observaciones: "",
};

function formatBytes(bytes?: number | null): string {
  if (!bytes) return "—";
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

async function fetchOptions<T>(url: string, params?: Record<string, unknown>) {
  const res = await api.get<{ data: T[] }>(url, { params });
  return res.data.data ?? [];
}

async function fetchMinutes(params: Record<string, string | number | undefined>) {
  const res = await api.get<ListResponse>("/minutes", { params });
  return res.data;
}

export function MinutesPage() {
  const user = useAuthStore((state) => state.user);
  const queryClient = useQueryClient();
  const [searchParams] = useSearchParams();

  const [cliente, setCliente] = useState(() => searchParams.get("cliente") ?? "");
  const [tarea, setTarea] = useState("");
  const [page, setPage] = useState(1);

  const [editorOpen, setEditorOpen] = useState(false);
  const [editing, setEditing] = useState<Minuta | null>(null);
  const [detail, setDetail] = useState<Minuta | null>(null);
  const [form, setForm] = useState<FormState>(EMPTY_FORM);
  const [archivo, setArchivo] = useState<File | null>(null);
  const [notice, setNotice] = useState("");
  const [error, setError] = useState("");

  const isManagement =
    user?.rol === ROLES.DUENO ||
    user?.rol === ROLES.ADMINISTRADOR ||
    user?.rol === ROLES.COORDINADOR;

  const clientsQuery = useQuery({
    queryKey: ["clients", "options", "minutes"],
    queryFn: () => fetchOptions<ClienteOption>("/clients/options"),
    staleTime: 60_000,
  });

  const tasksQuery = useQuery({
    queryKey: ["tasks", "options", "minutes"],
    queryFn: () => fetchOptions<TaskOption>("/tasks/options", { incluir_completadas: true }),
    staleTime: 60_000,
  });

  const params = useMemo(
    () => ({
      cliente: cliente ? Number(cliente) : undefined,
      tarea: tarea ? Number(tarea) : undefined,
      page,
    }),
    [cliente, tarea, page],
  );

  const query = useQuery({
    queryKey: ["minutes", params],
    queryFn: () => fetchMinutes(params),
    staleTime: 20_000,
  });

  const invalidate = () => queryClient.invalidateQueries({ queryKey: ["minutes"] });

  const saveMutation = useMutation({
    mutationFn: async (payload: { form: FormState; archivo: File | null }) => {
      const body = new FormData();
      body.append("tipo", payload.form.tipo);
      body.append("titulo", payload.form.titulo.trim());
      body.append("fecha_reunion", payload.form.fecha_reunion);
      if (payload.form.cliente_id) body.append("cliente_id", payload.form.cliente_id);
      if (payload.form.tarea_id) body.append("tarea_id", payload.form.tarea_id);
      if (payload.form.observaciones.trim()) {
        body.append("observaciones", payload.form.observaciones.trim());
      }
      if (payload.archivo) body.append("archivo", payload.archivo);

      if (editing) {
        await api.put(`/minutes/${editing.id}`, body);
      } else {
        await api.post("/minutes", body);
      }
    },
    onSuccess: () => {
      setNotice(editing ? "Minuta actualizada." : "Minuta registrada.");
      setError("");
      setEditorOpen(false);
      setEditing(null);
      setArchivo(null);
      invalidate();
    },
    onError: (err) => setError(getErrorMessage(err)),
  });

  const deleteMutation = useMutation({
    mutationFn: async (id: number) => {
      await api.delete(`/minutes/${id}`);
    },
    onSuccess: () => {
      setNotice("Minuta eliminada.");
      setError("");
      setDetail(null);
      invalidate();
    },
    onError: (err) => setError(getErrorMessage(err)),
  });

  const downloadMutation = useMutation({
    mutationFn: async (minuta: Minuta) => {
      const res = await api.get(`/minutes/${minuta.id}/download`, { responseType: "blob" });
      const url = URL.createObjectURL(res.data as Blob);
      const link = document.createElement("a");
      link.href = url;
      link.download = minuta.archivo_nombre;
      document.body.appendChild(link);
      link.click();
      link.remove();
      URL.revokeObjectURL(url);
    },
    onError: (err) => setError(getErrorMessage(err)),
  });

  const canEdit = (minuta: Minuta) => isManagement || minuta.cargada_por === user?.id;

  const openCreate = () => {
    setEditing(null);
    setForm(EMPTY_FORM);
    setArchivo(null);
    setError("");
    setEditorOpen(true);
  };

  const openEdit = (minuta: Minuta) => {
    setEditing(minuta);
    setForm({
      tipo: minuta.tipo,
      cliente_id: minuta.cliente_id ? String(minuta.cliente_id) : "",
      tarea_id: minuta.tarea_id ? String(minuta.tarea_id) : "",
      titulo: minuta.titulo,
      fecha_reunion: minuta.fecha_reunion,
      observaciones: minuta.observaciones ?? "",
    });
    setArchivo(null);
    setError("");
    setEditorOpen(true);
  };

  const onFileChange = (file: File | null) => {
    setError("");
    if (!file) {
      setArchivo(null);
      return;
    }
    if (!MIME_PERMITIDOS.includes(file.type)) {
      setError("El archivo debe ser PDF, DOCX, XLSX, JPG o PNG.");
      setArchivo(null);
      return;
    }
    if (file.size < 1 || file.size > MAX_BYTES) {
      setError("El archivo debe pesar entre 1 byte y 10 MB.");
      setArchivo(null);
      return;
    }
    setArchivo(file);
  };

  const items = query.data?.data ?? [];
  const meta = query.data?.meta;
  const total = meta?.total ?? items.length;
  const tareasFiltradas = (tasksQuery.data ?? []).filter(
    (option) => !form.cliente_id || String(option.cliente_id) === form.cliente_id,
  );

  const submit = (event: FormEvent) => {
    event.preventDefault();
    saveMutation.mutate({ form, archivo });
  };

  return (
    <div className="mx-auto flex w-full max-w-[1440px] flex-col gap-4">
      <PageHeader
        eyebrow="Módulo 7 · Minutas y acuerdos"
        title="Minutas y Acuerdos"
        description="Documentos de reuniones y compromisos, ligados a un cliente o a una tarea."
        actions={
          <button type="button" className={BTN_PRIMARY} onClick={openCreate}>
            <Plus size={16} /> Nueva minuta
          </button>
        }
      />

      {notice && <Notice tone="success">{notice}</Notice>}
      {error && <Notice tone="danger">{error}</Notice>}

      <section className="card flex flex-wrap items-end gap-3 p-3">
        <label className="flex min-w-52 flex-col gap-1">
          <span className="text-[10px] font-semibold uppercase tracking-wide text-muted">Cliente</span>
          <select
            value={cliente}
            onChange={(event) => {
              setCliente(event.target.value);
              setPage(1);
            }}
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
        <label className="flex min-w-64 flex-col gap-1">
          <span className="text-[10px] font-semibold uppercase tracking-wide text-muted">Tarea</span>
          <select
            value={tarea}
            onChange={(event) => {
              setTarea(event.target.value);
              setPage(1);
            }}
            className="rounded-lg border border-line bg-surface px-3 py-2 text-sm text-ink"
          >
            <option value="">Todas las tareas</option>
            {(tasksQuery.data ?? []).map((option) => (
              <option key={option.id} value={option.id}>
                {option.titulo} · {option.cliente_nombre ?? "Sin cliente"}
              </option>
            ))}
          </select>
        </label>
        <span className="ml-auto pb-2 text-xs text-muted">{total} minutas</span>
      </section>

      {query.isLoading && <LoadingState label="Cargando minutas…" />}
      {query.isError && <ErrorState message={getErrorMessage(query.error)} />}

      {!query.isLoading && !query.isError && items.length === 0 && (
        <EmptyState
          title="Sin minutas registradas"
          description="Sube el primer documento de una reunión o acuerdo."
          icon={<FileText size={22} />}
          action={
            <button type="button" className={BTN_PRIMARY} onClick={openCreate}>
              <Plus size={15} /> Nueva minuta
            </button>
          }
        />
      )}

      {items.length > 0 && (
        <section className="card overflow-x-auto">
          <table className="w-full text-left">
            <thead className="border-b border-line bg-app/60">
              <tr className="text-[10px] font-semibold uppercase tracking-[0.1em] text-muted">
                <th className="px-5 py-3">Documento</th>
                <th className="px-4 py-3">Tipo</th>
                <th className="px-4 py-3">Reunión</th>
                <th className="px-4 py-3">Cliente</th>
                <th className="px-4 py-3">Tarea</th>
                <th className="px-4 py-3">Archivo</th>
                <th className="px-4 py-3">Cargó</th>
                <th className="px-4 py-3 text-right">Acciones</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-line">
              {items.map((minuta) => (
                <tr key={minuta.id} className="hover:bg-app/50">
                  <td className="max-w-64 truncate px-5 py-3 text-sm font-semibold text-ink">
                    {minuta.titulo}
                  </td>
                  <td className="px-4 py-3">
                    <Badge
                      className={
                        minuta.tipo === "CLIENTE"
                          ? "bg-sky-50 text-sky-700 ring-sky-200"
                          : "bg-slate-100 text-slate-600 ring-slate-200"
                      }
                    >
                      {TIPO_MINUTA_LABELS[minuta.tipo] ?? minuta.tipo}
                    </Badge>
                  </td>
                  <td className="px-4 py-3 text-xs text-muted">{formatDate(minuta.fecha_reunion)}</td>
                  <td className="px-4 py-3 text-xs text-muted">{minuta.cliente_nombre ?? "—"}</td>
                  <td className="max-w-56 truncate px-4 py-3 text-xs text-muted">
                    {minuta.tarea_titulo ?? "—"}
                  </td>
                  <td className="max-w-56 truncate px-4 py-3 text-xs text-muted">
                    <span title={minuta.archivo_nombre}>{minuta.archivo_nombre}</span>
                    <span className="ml-1 text-[10px]">({formatBytes(minuta.archivo_bytes)})</span>
                  </td>
                  <td className="px-4 py-3 text-xs text-muted">{minuta.cargador_nombre ?? "—"}</td>
                  <td className="px-4 py-3">
                    <div className="flex justify-end gap-1">
                      <button type="button" className={BTN_GHOST} onClick={() => setDetail(minuta)}>
                        <Eye size={14} /> Ver
                      </button>
                      <button
                        type="button"
                        className={BTN_GHOST}
                        onClick={() => downloadMutation.mutate(minuta)}
                        disabled={downloadMutation.isPending}
                      >
                        <Download size={14} /> Descargar
                      </button>
                      {canEdit(minuta) && (
                        <button type="button" className={BTN_GHOST} onClick={() => openEdit(minuta)}>
                          <Pencil size={14} /> Editar
                        </button>
                      )}
                      {isManagement && (
                        <button
                          type="button"
                          className={BTN_DANGER}
                          onClick={() => {
                            if (window.confirm(`¿Eliminar la minuta "${minuta.titulo}"?`)) {
                              deleteMutation.mutate(minuta.id);
                            }
                          }}
                        >
                          <Trash2 size={14} /> Eliminar
                        </button>
                      )}
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
        onClose={() => setEditorOpen(false)}
        title={editing ? "Editar minuta" : "Nueva minuta"}
        description="Adjunta el documento de la reunión. Formatos: PDF, DOCX, XLSX, JPG o PNG (máx. 10 MB)."
        wide
      >
        <form className="grid gap-3 sm:grid-cols-2" onSubmit={submit}>
          <FormField label="Tipo de minuta" required>
            <select
              value={form.tipo}
              onChange={(event) => {
                const tipo = event.target.value;
                setForm((prev) => ({
                  ...prev,
                  tipo,
                  cliente_id: tipo === "PERSONAL" ? "" : prev.cliente_id,
                  tarea_id: tipo === "PERSONAL" ? "" : prev.tarea_id,
                }));
              }}
              className={INPUT_CLASS}
            >
              {TIPOS_MINUTA.map((value) => (
                <option key={value} value={value}>
                  {TIPO_MINUTA_LABELS[value]}
                </option>
              ))}
            </select>
          </FormField>
          <FormField label="Fecha de reunión" required>
            <input
              type="date"
              value={form.fecha_reunion}
              onChange={(event) => setForm({ ...form, fecha_reunion: event.target.value })}
              className={INPUT_CLASS}
            />
          </FormField>
          <FormField label="Título" required className="sm:col-span-2">
            <input
              value={form.titulo}
              maxLength={100}
              onChange={(event) => setForm({ ...form, titulo: event.target.value })}
              placeholder="Ej. Reunión de cierre mensual"
              className={INPUT_CLASS}
            />
          </FormField>
          <FormField label="Cliente" required={form.tipo === "CLIENTE"}>
            <select
              value={form.cliente_id}
              onChange={(event) => {
                const value = event.target.value;
                setForm((prev) => ({
                  ...prev,
                  cliente_id: value,
                  tarea_id: value ? prev.tarea_id : "",
                }));
              }}
              className={INPUT_CLASS}
              disabled={form.tipo === "PERSONAL"}
            >
              <option value="">Sin cliente</option>
              {(clientsQuery.data ?? []).map((option) => (
                <option key={option.id} value={option.id}>
                  {option.nombre_completo}
                </option>
              ))}
            </select>
          </FormField>
          <FormField label="Tarea" hint="Requiere un cliente">
            <select
              value={form.tarea_id}
              onChange={(event) => setForm({ ...form, tarea_id: event.target.value })}
              className={INPUT_CLASS}
              disabled={!form.cliente_id}
            >
              <option value="">Sin tarea</option>
              {tareasFiltradas.map((option) => (
                <option key={option.id} value={option.id}>
                  {option.titulo}
                </option>
              ))}
            </select>
          </FormField>
          <FormField
            label="Archivo"
            required={!editing}
            className="sm:col-span-2"
            hint={editing ? "Selecciona un archivo solo si quieres reemplazar el actual." : undefined}
          >
            <input
              type="file"
              accept={EXTENSIONES}
              onChange={(event) => onFileChange(event.target.files?.[0] ?? null)}
              className={INPUT_CLASS}
            />
            {editing && (
              <span className="text-xs text-muted">Actual: {editing.archivo_nombre}</span>
            )}
          </FormField>
          <FormField label="Observaciones" className="sm:col-span-2" hint="Máximo 2,000 caracteres">
            <textarea
              value={form.observaciones}
              rows={4}
              maxLength={2000}
              onChange={(event) => setForm({ ...form, observaciones: event.target.value })}
              className={INPUT_CLASS}
            />
          </FormField>
          <div className="flex justify-end gap-2 sm:col-span-2">
            <button
              type="button"
              className={BTN_SECONDARY}
              onClick={() => setEditorOpen(false)}
              disabled={saveMutation.isPending}
            >
              Cancelar
            </button>
            <button
              type="submit"
              className={BTN_PRIMARY}
              disabled={
                saveMutation.isPending ||
                !form.fecha_reunion ||
                form.titulo.trim().length < 3 ||
                (form.tipo === "CLIENTE" && !form.cliente_id) ||
                (!editing && !archivo)
              }
            >
              {saveMutation.isPending
                ? "Guardando…"
                : editing
                  ? "Guardar cambios"
                  : "Registrar minuta"}
            </button>
          </div>
        </form>
      </Modal>

      <Modal
        open={detail !== null}
        onClose={() => setDetail(null)}
        title={detail?.titulo ?? "Minuta"}
        description={
          detail
            ? `${formatDate(detail.fecha_reunion)} · ${detail.cargador_nombre ?? "Autor desconocido"}`
            : undefined
        }
        wide
        footer={
          detail ? (
            <>
              <button type="button" className={BTN_SECONDARY} onClick={() => setDetail(null)}>
                Cerrar
              </button>
              <button
                type="button"
                className={BTN_SECONDARY}
                onClick={() => downloadMutation.mutate(detail)}
                disabled={downloadMutation.isPending}
              >
                <Download size={15} /> Descargar
              </button>
              {canEdit(detail) && (
                <button
                  type="button"
                  className={BTN_PRIMARY}
                  onClick={() => {
                    setDetail(null);
                    openEdit(detail);
                  }}
                >
                  <Pencil size={15} /> Editar
                </button>
              )}
            </>
          ) : undefined
        }
      >
        {detail && (
          <div className="flex flex-col gap-4 text-sm">
            <div className="grid gap-2 sm:grid-cols-2">
              <p>
                <span className="text-[11px] font-semibold uppercase tracking-wide text-muted">Tipo</span>
                <br />
                {TIPO_MINUTA_LABELS[detail.tipo] ?? detail.tipo}
              </p>
              <p>
                <span className="text-[11px] font-semibold uppercase tracking-wide text-muted">Cliente</span>
                <br />
                {detail.cliente_nombre ?? "Sin cliente"}
              </p>
              <p>
                <span className="text-[11px] font-semibold uppercase tracking-wide text-muted">Tarea</span>
                <br />
                {detail.tarea_titulo ?? "Sin tarea"}
              </p>
              <p>
                <span className="text-[11px] font-semibold uppercase tracking-wide text-muted">Archivo</span>
                <br />
                {detail.archivo_nombre} ({formatBytes(detail.archivo_bytes)})
              </p>
            </div>
            <div>
              <p className="text-[11px] font-semibold uppercase tracking-wide text-muted">
                Observaciones
              </p>
              <p className="mt-1 whitespace-pre-wrap rounded-lg bg-app/60 p-3 text-ink">
                {detail.observaciones ?? "—"}
              </p>
            </div>
          </div>
        )}
      </Modal>
    </div>
  );
}
