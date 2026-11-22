import { useMemo, useState, type FormEvent } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  ListTree,
  Loader2,
  Pencil,
  Plus,
  Power,
  Search,
} from "lucide-react";
import { api } from "@/shared/api/client";
import { useAuthStore } from "@/shared/auth/authStore";
import { ROLES } from "@/shared/constants/roles";
import {
  BTN_DANGER,
  BTN_GHOST,
  BTN_PRIMARY,
  BTN_SECONDARY,
  INPUT_CLASS,
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
import { getErrorMessage } from "@/shared/utils/utils";

interface Subcategoria {
  id: number;
  nombre: string;
  activa: boolean;
  orden: number;
}

interface Categoria {
  id: number;
  nombre: string;
  activa: boolean;
  orden: number;
  subcategorias?: Subcategoria[];
}

interface CatalogResponse {
  data: Categoria[];
}

interface EditorState {
  id: number | null;
  padreId: number | null;
  nombre: string;
  orden: string;
  activa: boolean;
}

const EMPTY_EDITOR: EditorState = {
  id: null,
  padreId: null,
  nombre: "",
  orden: "0",
  activa: true,
};

async function fetchCatalog(q: string, soloActivas: boolean): Promise<Categoria[]> {
  const res = await api.get<CatalogResponse>("/catalog", {
    params: {
      q: q.trim() || undefined,
      solo_activas: soloActivas || undefined,
    },
  });
  return res.data.data ?? [];
}

export function CatalogPage() {
  const user = useAuthStore((state) => state.user);
  const queryClient = useQueryClient();
  const [q, setQ] = useState("");
  const [soloActivas, setSoloActivas] = useState(false);
  const [editor, setEditor] = useState<EditorState | null>(null);
  const [notice, setNotice] = useState("");
  const [error, setError] = useState("");
  const debounced = q.trim();

  const canManage = user?.rol === ROLES.DUENO || user?.rol === ROLES.ADMINISTRADOR;

  const query = useQuery({
    queryKey: ["catalog", debounced, soloActivas],
    queryFn: () => fetchCatalog(debounced, soloActivas),
    staleTime: 30_000,
  });

  const invalidate = () => queryClient.invalidateQueries({ queryKey: ["catalog"] });

  const saveMutation = useMutation({
    mutationFn: async (state: EditorState) => {
      const body = {
        nombre: state.nombre.trim(),
        orden: Number(state.orden) || 0,
        activa: state.activa,
      };
      if (state.id) {
        await api.put(`/catalog/${state.id}`, body);
      } else {
        await api.post("/catalog", { ...body, padre_id: state.padreId ?? null });
      }
    },
    onSuccess: () => {
      setNotice(editor?.id ? "Entrada actualizada." : "Entrada creada.");
      setError("");
      setEditor(null);
      invalidate();
    },
    onError: (err) => setError(getErrorMessage(err)),
  });

  const deactivateMutation = useMutation({
    mutationFn: async (id: number) => {
      await api.post(`/catalog/${id}/deactivate`);
    },
    onSuccess: () => {
      setNotice("Entrada desactivada.");
      setError("");
      invalidate();
    },
    onError: (err) => setError(getErrorMessage(err)),
  });

  const items = useMemo(() => query.data ?? [], [query.data]);
  const totalSubs = useMemo(
    () => items.reduce((acc, c) => acc + (c.subcategorias?.length ?? 0), 0),
    [items],
  );

  const openCreateRoot = () => {
    setError("");
    setEditor({ ...EMPTY_EDITOR });
  };

  const openCreateSub = (categoria: Categoria) => {
    setError("");
    setEditor({ ...EMPTY_EDITOR, padreId: categoria.id });
  };

  const openEdit = (entrada: { id: number; nombre: string; orden: number; activa: boolean }, padreId: number | null) => {
    setError("");
    setEditor({
      id: entrada.id,
      padreId,
      nombre: entrada.nombre,
      orden: String(entrada.orden),
      activa: entrada.activa,
    });
  };

  const deactivate = (entrada: { id: number; nombre: string }, esRaiz: boolean) => {
    const extra = esRaiz && canManage ? "\n\nTambién se desactivarán sus subcategorías." : "";
    if (window.confirm(`¿Desactivar "${entrada.nombre}"?${extra}`)) {
      deactivateMutation.mutate(entrada.id);
    }
  };

  const parentName = editor?.padreId
    ? items.find((categoria) => categoria.id === editor.padreId)?.nombre ?? "Categoría"
    : null;

  const submit = (event: FormEvent) => {
    event.preventDefault();
    if (editor) saveMutation.mutate(editor);
  };

  return (
    <div className="mx-auto flex w-full max-w-[1240px] flex-col gap-4">
      <PageHeader
        eyebrow="Módulo 4 · Catálogo de proyectos y actividades"
        title="Catálogo de Servicios"
        description="Árbol de categorías y subcategorías disponibles para clasificar tareas y obligaciones."
        actions={
          canManage ? (
            <button type="button" className={BTN_PRIMARY} onClick={openCreateRoot}>
              <Plus size={16} /> Nueva categoría
            </button>
          ) : (
            <label className="inline-flex items-center gap-2 text-sm text-ink">
              <input
                type="checkbox"
                checked={soloActivas}
                onChange={(event) => setSoloActivas(event.target.checked)}
                className="size-4 rounded border-line accent-navy-900"
              />
              Solo activas
            </label>
          )
        }
      />

      {notice && <Notice tone="success">{notice}</Notice>}
      {error && <Notice tone="danger">{error}</Notice>}

      <div className="card flex items-center gap-2 p-3">
        <Search size={16} className="text-muted" />
        <input
          type="search"
          value={q}
          onChange={(event) => setQ(event.target.value)}
          placeholder="Buscar categoría o subcategoría…"
          className="w-full bg-transparent text-sm text-ink outline-none placeholder:text-muted/70"
        />
        {canManage && (
          <label className="inline-flex shrink-0 items-center gap-2 border-l border-line pl-3 text-sm text-ink">
            <input
              type="checkbox"
              checked={soloActivas}
              onChange={(event) => setSoloActivas(event.target.checked)}
              className="size-4 rounded border-line accent-navy-900"
            />
            Solo activas
          </label>
        )}
      </div>

      {query.isLoading && <LoadingState label="Cargando catálogo…" />}
      {query.isError && <ErrorState message={getErrorMessage(query.error)} />}

      {!query.isLoading && !query.isError && items.length === 0 && (
        <EmptyState
          title="Sin resultados"
          description="Ajusta la búsqueda o registra una nueva categoría."
          icon={<ListTree size={22} />}
          action={
            canManage ? (
              <button type="button" className={BTN_PRIMARY} onClick={openCreateRoot}>
                <Plus size={15} /> Nueva categoría
              </button>
            ) : undefined
          }
        />
      )}

      {!query.isLoading && !query.isError && items.length > 0 && (
        <section className="flex flex-col gap-3">
          <p className="text-[11px] text-muted">
            {items.length} categorías · {totalSubs} subcategorías
          </p>
          <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-3">
            {items.map((categoria) => (
              <article key={categoria.id} className="card flex flex-col p-4">
                <header className="flex items-start justify-between gap-2">
                  <div>
                    <h2 className="font-display text-base font-bold text-ink">{categoria.nombre}</h2>
                    <p className="text-[10px] uppercase tracking-wide text-muted">Orden {categoria.orden}</p>
                  </div>
                  <Badge
                    className={
                      categoria.activa
                        ? "bg-emerald-50 text-emerald-700 ring-emerald-200"
                        : "bg-slate-100 text-slate-600 ring-slate-200"
                    }
                  >
                    {categoria.activa ? "Activa" : "Inactiva"}
                  </Badge>
                </header>

                {categoria.subcategorias && categoria.subcategorias.length > 0 ? (
                  <ul className="mt-3 flex flex-col gap-1.5">
                    {categoria.subcategorias.map((sub) => (
                      <li
                        key={sub.id}
                        className="group flex items-center justify-between gap-2 rounded-lg bg-app/60 px-3 py-2 text-xs"
                      >
                        <span className="min-w-0 flex-1 truncate font-medium text-ink">{sub.nombre}</span>
                        <Badge
                          className={
                            sub.activa
                              ? "bg-emerald-50 text-emerald-700 ring-emerald-200"
                              : "bg-slate-100 text-slate-600 ring-slate-200"
                          }
                        >
                          {sub.activa ? "Activa" : "Inactiva"}
                        </Badge>
                        {canManage && (
                          <span className="flex shrink-0 items-center gap-0.5">
                            <button
                              type="button"
                              className="grid size-6 place-items-center rounded text-muted hover:bg-surface hover:text-ink"
                              title="Editar subcategoría"
                              onClick={() => openEdit(sub, categoria.id)}
                            >
                              <Pencil size={12} />
                            </button>
                            {sub.activa && (
                              <button
                                type="button"
                                className="grid size-6 place-items-center rounded text-muted hover:bg-rose-50 hover:text-rose-700"
                                title="Desactivar subcategoría"
                                onClick={() => deactivate(sub, false)}
                              >
                                <Power size={12} />
                              </button>
                            )}
                          </span>
                        )}
                      </li>
                    ))}
                  </ul>
                ) : (
                  <p className="mt-3 text-[11px] italic text-muted">Sin subcategorías registradas.</p>
                )}

                {canManage && (
                  <div className="mt-auto flex flex-wrap items-center gap-1 border-t border-line pt-3">
                    <button type="button" className={BTN_GHOST} onClick={() => openCreateSub(categoria)}>
                      <Plus size={13} /> Subcategoría
                    </button>
                    <button type="button" className={BTN_GHOST} onClick={() => openEdit(categoria, null)}>
                      <Pencil size={13} /> Editar
                    </button>
                    {categoria.activa && (
                      <button type="button" className={BTN_DANGER} onClick={() => deactivate(categoria, true)}>
                        <Power size={13} /> Desactivar
                      </button>
                    )}
                  </div>
                )}
              </article>
            ))}
          </div>
        </section>
      )}

      <Modal
        open={editor !== null}
        onClose={() => setEditor(null)}
        title={editor?.id ? "Editar entrada del catálogo" : editor?.padreId ? "Nueva subcategoría" : "Nueva categoría"}
        description={
          editor?.id
            ? "Puedes ajustar el nombre, el orden y el estatus."
            : editor?.padreId
              ? `Se agregará dentro de ${parentName}.`
              : "Se agregará como categoría raíz del catálogo."
        }
      >
        <form className="grid gap-3" onSubmit={submit}>
          <FormField label="Nombre" required hint="Entre 1 y 80 caracteres">
            <input
              value={editor?.nombre ?? ""}
              maxLength={80}
              onChange={(event) =>
                setEditor((prev) => (prev ? { ...prev, nombre: event.target.value } : prev))
              }
              className={INPUT_CLASS}
            />
          </FormField>
          <FormField label="Orden" hint="Menor número aparece primero">
            <input
              type="number"
              min={0}
              max={9999}
              value={editor?.orden ?? "0"}
              onChange={(event) =>
                setEditor((prev) => (prev ? { ...prev, orden: event.target.value } : prev))
              }
              className={INPUT_CLASS}
            />
          </FormField>
          {editor?.id ? (
            <label className="inline-flex items-center gap-2 text-sm text-ink">
              <input
                type="checkbox"
                checked={editor.activa}
                onChange={(event) =>
                  setEditor((prev) => (prev ? { ...prev, activa: event.target.checked } : prev))
                }
                className="size-4 rounded border-line accent-navy-900"
              />
              Entrada activa
            </label>
          ) : (
            <label className="inline-flex items-center gap-2 text-sm text-ink">
              <input
                type="checkbox"
                checked={editor?.activa ?? true}
                onChange={(event) =>
                  setEditor((prev) => (prev ? { ...prev, activa: event.target.checked } : prev))
                }
                className="size-4 rounded border-line accent-navy-900"
              />
              Crear como activa
            </label>
          )}
          {saveMutation.isPending && (
            <p className="flex items-center gap-2 text-xs text-muted">
              <Loader2 size={13} className="animate-spin" /> Guardando…
            </p>
          )}
          <div className="flex justify-end gap-2">
            <button type="button" className={BTN_SECONDARY} onClick={() => setEditor(null)} disabled={saveMutation.isPending}>
              Cancelar
            </button>
            <button
              type="submit"
              className={BTN_PRIMARY}
              disabled={saveMutation.isPending || !editor?.nombre.trim()}
            >
              {editor?.id ? "Guardar cambios" : "Crear entrada"}
            </button>
          </div>
        </form>
      </Modal>
    </div>
  );
}
