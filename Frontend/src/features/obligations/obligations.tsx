import { useMemo, useState, type FormEvent } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { useSearchParams } from "react-router-dom";
import { Pencil, Plus, Repeat, Power } from "lucide-react";
import { api } from "@/shared/api/client";
import { useAuthStore } from "@/shared/auth/authStore";
import { ROLES } from "@/shared/constants/roles";
import {
  BTN_DANGER,
  BTN_GHOST,
  BTN_PRIMARY,
  BTN_SECONDARY,
  INPUT_CLASS,
  PERIODICIDADES,
  PERIODICIDAD_LABELS,
  PRIORIDADES,
  PRIORIDAD_BADGE,
  PRIORIDAD_LABELS,
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

interface ClienteOption {
  id: number;
  nombre_completo: string;
  estatus: string;
}

interface UserOption {
  id: number;
  nombre_completo: string;
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

interface Obligacion {
  id: number;
  cliente_id: number;
  cliente_nombre: string | null;
  categoria_id: number;
  categoria_nombre: string | null;
  responsable_id: number;
  responsable_nombre: string | null;
  periodicidad: string;
  dia_vencimiento: number;
  fecha_inicio: string;
  prioridad: string;
  activa: boolean;
}

interface ListResponse {
  data: Obligacion[];
  meta?: { page: number; per_page: number; total: number; pages?: number };
}

interface FormState {
  cliente_id: string;
  categoria_id: string;
  responsable_id: string;
  periodicidad: string;
  dia_vencimiento: string;
  fecha_inicio: string;
  prioridad: string;
  activa: boolean;
}

const EMPTY_FORM: FormState = {
  cliente_id: "",
  categoria_id: "",
  responsable_id: "",
  periodicidad: "MENSUAL",
  dia_vencimiento: "20",
  fecha_inicio: todayISO(),
  prioridad: "MEDIA",
  activa: true,
};

function maxDia(periodicidad: string): number {
  return periodicidad === "SEMANAL" ? 7 : 31;
}

async function fetchOptions<T>(url: string, params?: Record<string, unknown>) {
  const res = await api.get<{ data: T[] }>(url, { params });
  return res.data.data ?? [];
}

async function fetchObligations(params: Record<string, string | number | boolean | undefined>) {
  const res = await api.get<ListResponse>("/obligations", { params });
  return res.data;
}

export function ObligationsPage() {
  const user = useAuthStore((state) => state.user);
  const queryClient = useQueryClient();
  const [searchParams] = useSearchParams();

  const [cliente, setCliente] = useState(() => searchParams.get("cliente") ?? "");
  const [soloActivas, setSoloActivas] = useState(false);
  const [page, setPage] = useState(1);

  const [editorOpen, setEditorOpen] = useState(false);
  const [editing, setEditing] = useState<Obligacion | null>(null);
  const [form, setForm] = useState<FormState>(EMPTY_FORM);
  const [notice, setNotice] = useState("");
  const [error, setError] = useState("");

  const canManage =
    user?.rol === ROLES.DUENO ||
    user?.rol === ROLES.ADMINISTRADOR ||
    user?.rol === ROLES.COORDINADOR;
  const canDeactivate = user?.rol === ROLES.DUENO || user?.rol === ROLES.ADMINISTRADOR;

  const clientsQuery = useQuery({
    queryKey: ["clients", "options", "obligations"],
    queryFn: () => fetchOptions<ClienteOption>("/clients/options"),
    staleTime: 60_000,
  });

  const usersQuery = useQuery({
    queryKey: ["users", "options", "obligations"],
    queryFn: () => fetchOptions<UserOption>("/users/options"),
    staleTime: 60_000,
  });

  const catalogQuery = useQuery({
    queryKey: ["catalog", "options", "obligations"],
    queryFn: async () => {
      const res = await api.get<{ data: Categoria[] }>("/catalog", {
        params: { solo_activas: true },
      });
      return res.data.data ?? [];
    },
    staleTime: 60_000,
  });

  const categoryRows = useMemo(() => {
    const rows: Array<{ id: number; label: string }> = [];
    for (const categoria of catalogQuery.data ?? []) {
      rows.push({ id: categoria.id, label: categoria.nombre });
      for (const sub of categoria.subcategorias ?? []) {
        rows.push({ id: sub.id, label: `${categoria.nombre} / ${sub.nombre}` });
      }
    }
    return rows;
  }, [catalogQuery.data]);

  const params = useMemo(
    () => ({
      cliente: cliente ? Number(cliente) : undefined,
      solo_activas: soloActivas || undefined,
      page,
    }),
    [cliente, soloActivas, page],
  );

  const query = useQuery({
    queryKey: ["obligations", params],
    queryFn: () => fetchObligations(params),
    staleTime: 20_000,
  });

  const invalidate = () => queryClient.invalidateQueries({ queryKey: ["obligations"] });

  const saveMutation = useMutation({
    mutationFn: async (payload: FormState) => {
      const body = {
        cliente_id: Number(payload.cliente_id),
        categoria_id: Number(payload.categoria_id),
        responsable_id: Number(payload.responsable_id),
        periodicidad: payload.periodicidad,
        dia_vencimiento: Number(payload.dia_vencimiento),
        fecha_inicio: payload.fecha_inicio,
        prioridad: payload.prioridad,
        ...(editing ? { activa: payload.activa } : {}),
      };
      if (editing) {
        await api.put(`/obligations/${editing.id}`, body);
      } else {
        await api.post("/obligations", body);
      }
    },
    onSuccess: () => {
      setNotice(editing ? "Obligación actualizada." : "Obligación registrada.");
      setError("");
      setEditorOpen(false);
      setEditing(null);
      invalidate();
    },
    onError: (err) => setError(getErrorMessage(err)),
  });

  const deactivateMutation = useMutation({
    mutationFn: async (id: number) => {
      await api.post(`/obligations/${id}/deactivate`);
    },
    onSuccess: () => {
      setNotice("Obligación desactivada.");
      setError("");
      invalidate();
    },
    onError: (err) => setError(getErrorMessage(err)),
  });

  const openCreate = () => {
    setEditing(null);
    setForm(EMPTY_FORM);
    setError("");
    setEditorOpen(true);
  };

  const openEdit = (obligacion: Obligacion) => {
    setEditing(obligacion);
    setForm({
      cliente_id: String(obligacion.cliente_id),
      categoria_id: String(obligacion.categoria_id),
      responsable_id: String(obligacion.responsable_id),
      periodicidad: obligacion.periodicidad,
      dia_vencimiento: String(obligacion.dia_vencimiento),
      fecha_inicio: obligacion.fecha_inicio,
      prioridad: obligacion.prioridad,
      activa: obligacion.activa,
    });
    setError("");
    setEditorOpen(true);
  };

  const items = query.data?.data ?? [];
  const meta = query.data?.meta;
  const total = meta?.total ?? items.length;
  const diaMax = maxDia(form.periodicidad);

  const submit = (event: FormEvent) => {
    event.preventDefault();
    saveMutation.mutate(form);
  };

  return (
    <div className="mx-auto flex w-full max-w-[1440px] flex-col gap-4">
      <PageHeader
        eyebrow="Módulo 6 · Obligaciones periódicas"
        title="Obligaciones Periódicas"
        description="Declaraciones y trámites recurrentes por cliente, con responsable, periodicidad y día de vencimiento."
        actions={
          canManage ? (
            <button type="button" className={BTN_PRIMARY} onClick={openCreate}>
              <Plus size={16} /> Nueva obligación
            </button>
          ) : undefined
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
        <label className="inline-flex items-center gap-2 pb-2 text-sm text-ink">
          <input
            type="checkbox"
            checked={soloActivas}
            onChange={(event) => {
              setSoloActivas(event.target.checked);
              setPage(1);
            }}
            className="size-4 rounded border-line accent-navy-900"
          />
          Solo activas
        </label>
        <span className="ml-auto pb-2 text-xs text-muted">{total} obligaciones</span>
      </section>

      {query.isLoading && <LoadingState label="Cargando obligaciones…" />}
      {query.isError && <ErrorState message={getErrorMessage(query.error)} />}

      {!query.isLoading && !query.isError && items.length === 0 && (
        <EmptyState
          title="Sin obligaciones registradas"
          description="Registra la primera obligación periódica de un cliente."
          icon={<Repeat size={22} />}
          action={
            canManage ? (
              <button type="button" className={BTN_PRIMARY} onClick={openCreate}>
                <Plus size={15} /> Nueva obligación
              </button>
            ) : undefined
          }
        />
      )}

      {items.length > 0 && (
        <section className="card overflow-x-auto">
          <table className="w-full text-left">
            <thead className="border-b border-line bg-app/60">
              <tr className="text-[10px] font-semibold uppercase tracking-[0.1em] text-muted">
                <th className="px-5 py-3">Cliente</th>
                <th className="px-4 py-3">Categoría</th>
                <th className="px-4 py-3">Responsable</th>
                <th className="px-4 py-3">Periodicidad</th>
                <th className="px-4 py-3">Vence</th>
                <th className="px-4 py-3">Inicio</th>
                <th className="px-4 py-3">Prioridad</th>
                <th className="px-4 py-3">Estatus</th>
                <th className="px-4 py-3 text-right">Acciones</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-line">
              {items.map((obligacion) => (
                <tr key={obligacion.id} className="hover:bg-app/50">
                  <td className="px-5 py-3 text-sm font-semibold text-ink">
                    {obligacion.cliente_nombre ?? obligacion.cliente_id}
                  </td>
                  <td className="px-4 py-3 text-xs text-muted">
                    {obligacion.categoria_nombre ?? "—"}
                  </td>
                  <td className="px-4 py-3 text-xs text-muted">
                    {obligacion.responsable_nombre ?? "—"}
                  </td>
                  <td className="px-4 py-3 text-xs text-muted">
                    {PERIODICIDAD_LABELS[obligacion.periodicidad] ?? obligacion.periodicidad}
                  </td>
                  <td className="px-4 py-3 text-xs text-muted">
                    Día {obligacion.dia_vencimiento}
                  </td>
                  <td className="px-4 py-3 text-xs text-muted">
                    {formatDate(obligacion.fecha_inicio)}
                  </td>
                  <td className="px-4 py-3">
                    <Badge className={PRIORIDAD_BADGE[obligacion.prioridad]}>
                      {PRIORIDAD_LABELS[obligacion.prioridad] ?? obligacion.prioridad}
                    </Badge>
                  </td>
                  <td className="px-4 py-3">
                    <Badge
                      className={
                        obligacion.activa
                          ? "bg-emerald-50 text-emerald-700 ring-emerald-200"
                          : "bg-slate-100 text-slate-600 ring-slate-200"
                      }
                    >
                      {obligacion.activa ? "Activa" : "Inactiva"}
                    </Badge>
                  </td>
                  <td className="px-4 py-3">
                    <div className="flex justify-end gap-1">
                      {canManage && (
                        <button type="button" className={BTN_GHOST} onClick={() => openEdit(obligacion)}>
                          <Pencil size={14} /> Editar
                        </button>
                      )}
                      {canDeactivate && obligacion.activa && (
                        <button
                          type="button"
                          className={BTN_DANGER}
                          onClick={() => {
                            if (window.confirm("¿Desactivar esta obligación periódica?")) {
                              deactivateMutation.mutate(obligacion.id);
                            }
                          }}
                        >
                          <Power size={14} /> Desactivar
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
        title={editing ? "Editar obligación" : "Nueva obligación"}
        description="La obligación se repite según su periodicidad y vence el día indicado."
        wide
      >
        <form className="grid gap-3 sm:grid-cols-2" onSubmit={submit}>
          <FormField label="Cliente" required>
            <select
              value={form.cliente_id}
              onChange={(event) => setForm({ ...form, cliente_id: event.target.value })}
              className={INPUT_CLASS}
            >
              <option value="">Selecciona un cliente</option>
              {(clientsQuery.data ?? []).map((option) => (
                <option key={option.id} value={option.id}>
                  {option.nombre_completo}
                </option>
              ))}
            </select>
          </FormField>
          <FormField label="Categoría del catálogo" required>
            <select
              value={form.categoria_id}
              onChange={(event) => setForm({ ...form, categoria_id: event.target.value })}
              className={INPUT_CLASS}
            >
              <option value="">Selecciona una categoría</option>
              {categoryRows.map((row) => (
                <option key={row.id} value={row.id}>
                  {row.label}
                </option>
              ))}
            </select>
          </FormField>
          <FormField label="Responsable" required>
            <select
              value={form.responsable_id}
              onChange={(event) => setForm({ ...form, responsable_id: event.target.value })}
              className={INPUT_CLASS}
            >
              <option value="">Selecciona un responsable</option>
              {(usersQuery.data ?? []).map((option) => (
                <option key={option.id} value={option.id}>
                  {option.nombre_completo}
                </option>
              ))}
            </select>
          </FormField>
          <FormField label="Prioridad" required>
            <select
              value={form.prioridad}
              onChange={(event) => setForm({ ...form, prioridad: event.target.value })}
              className={INPUT_CLASS}
            >
              {PRIORIDADES.map((value) => (
                <option key={value} value={value}>
                  {PRIORIDAD_LABELS[value]}
                </option>
              ))}
            </select>
          </FormField>
          <FormField label="Periodicidad" required>
            <select
              value={form.periodicidad}
              onChange={(event) => {
                const periodicidad = event.target.value;
                setForm({
                  ...form,
                  periodicidad,
                  dia_vencimiento: String(
                    Math.min(Number(form.dia_vencimiento) || 1, maxDia(periodicidad)),
                  ),
                });
              }}
              className={INPUT_CLASS}
            >
              {PERIODICIDADES.map((value) => (
                <option key={value} value={value}>
                  {PERIODICIDAD_LABELS[value]}
                </option>
              ))}
            </select>
          </FormField>
          <FormField
            label="Día de vencimiento"
            required
            hint={form.periodicidad === "SEMANAL" ? "Del 1 al 7" : "Del 1 al 31"}
          >
            <input
              type="number"
              min={1}
              max={diaMax}
              value={form.dia_vencimiento}
              onChange={(event) => setForm({ ...form, dia_vencimiento: event.target.value })}
              className={INPUT_CLASS}
            />
          </FormField>
          <FormField label="Fecha de inicio" required className="sm:col-span-2">
            <input
              type="date"
              value={form.fecha_inicio}
              onChange={(event) => setForm({ ...form, fecha_inicio: event.target.value })}
              className={INPUT_CLASS}
            />
          </FormField>
          {editing && (
            <label className="inline-flex items-center gap-2 text-sm text-ink sm:col-span-2">
              <input
                type="checkbox"
                checked={form.activa}
                onChange={(event) => setForm({ ...form, activa: event.target.checked })}
                className="size-4 rounded border-line accent-navy-900"
              />
              Obligación activa
            </label>
          )}
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
                !form.cliente_id ||
                !form.categoria_id ||
                !form.responsable_id ||
                !form.fecha_inicio ||
                Number(form.dia_vencimiento) < 1 ||
                Number(form.dia_vencimiento) > diaMax
              }
            >
              {saveMutation.isPending
                ? "Guardando…"
                : editing
                  ? "Guardar cambios"
                  : "Crear obligación"}
            </button>
          </div>
        </form>
      </Modal>
    </div>
  );
}
