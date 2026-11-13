import { useMemo, useState, type FormEvent } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Eye, Mail, Pencil, Plus, RotateCcw } from "lucide-react";
import { api } from "@/shared/api/client";
import {
  BTN_GHOST,
  BTN_PRIMARY,
  BTN_SECONDARY,
  CLAVES_PLANTILLA,
  CLAVE_PLANTILLA_LABELS,
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
import { formatDateTime, getErrorMessage } from "@/shared/utils/utils";

interface Plantilla {
  id: number;
  clave: string;
  asunto: string;
  cuerpo: string;
  asunto_original: string;
  cuerpo_original: string;
  updated_at: string | null;
}

interface FormState {
  clave: string;
  asunto: string;
  cuerpo: string;
}

const EMPTY_FORM: FormState = {
  clave: "",
  asunto: "",
  cuerpo: "",
};

export function TemplatesPage() {
  const queryClient = useQueryClient();
  const [editorOpen, setEditorOpen] = useState(false);
  const [editing, setEditing] = useState<Plantilla | null>(null);
  const [preview, setPreview] = useState<Plantilla | null>(null);
  const [form, setForm] = useState<FormState>(EMPTY_FORM);
  const [notice, setNotice] = useState("");
  const [error, setError] = useState("");

  const query = useQuery({
    queryKey: ["templates"],
    queryFn: async () => {
      const res = await api.get<{ data: Plantilla[] }>("/templates");
      return res.data.data ?? [];
    },
    staleTime: 30_000,
  });

  const saveMutation = useMutation({
    mutationFn: async (payload: FormState) => {
      if (editing) {
        await api.put(`/templates/${editing.id}`, {
          asunto: payload.asunto.trim(),
          cuerpo: payload.cuerpo.trim(),
        });
      } else {
        await api.post("/templates", {
          clave: payload.clave,
          asunto: payload.asunto.trim(),
          cuerpo: payload.cuerpo.trim(),
        });
      }
    },
    onSuccess: () => {
      setNotice(editing ? "Plantilla actualizada." : "Plantilla creada.");
      setError("");
      setEditorOpen(false);
      setEditing(null);
      queryClient.invalidateQueries({ queryKey: ["templates"] });
    },
    onError: (err) => setError(getErrorMessage(err)),
  });

  const items = useMemo(() => query.data ?? [], [query.data]);

  const availableKeys = useMemo(
    () => CLAVES_PLANTILLA.filter((clave) => !items.some((item) => item.clave === clave)),
    [items],
  );

  const openCreate = () => {
    setEditing(null);
    setForm({ ...EMPTY_FORM, clave: availableKeys[0] ?? "" });
    setError("");
    setEditorOpen(true);
  };

  const openEdit = (plantilla: Plantilla) => {
    setEditing(plantilla);
    setForm({
      clave: plantilla.clave,
      asunto: plantilla.asunto,
      cuerpo: plantilla.cuerpo,
    });
    setError("");
    setEditorOpen(true);
  };

  const restoreOriginal = () => {
    if (!editing) return;
    setForm({
      clave: editing.clave,
      asunto: editing.asunto_original,
      cuerpo: editing.cuerpo_original,
    });
    setNotice("");
  };

  const submit = (event: FormEvent) => {
    event.preventDefault();
    saveMutation.mutate(form);
  };

  return (
    <div className="mx-auto flex w-full max-w-[1240px] flex-col gap-4">
      <PageHeader
        eyebrow="Módulo 14 · Plantillas de notificación"
        title="Plantillas de Notificación"
        description="Asuntos y cuerpos de los correos automáticos de asignación, vencimiento y tareas completadas."
        actions={
          <button
            type="button"
            className={BTN_PRIMARY}
            onClick={openCreate}
            disabled={availableKeys.length === 0}
          >
            <Plus size={16} /> Nueva plantilla
          </button>
        }
      />

      {notice && <Notice tone="success">{notice}</Notice>}
      {error && <Notice tone="danger">{error}</Notice>}

      {query.isLoading && <LoadingState label="Cargando plantillas…" />}
      {query.isError && <ErrorState message={getErrorMessage(query.error)} />}

      {!query.isLoading && !query.isError && items.length === 0 && (
        <EmptyState
          title="Sin plantillas registradas"
          description="Crea las plantillas de asignación, vencimiento y tarea completada."
          icon={<Mail size={22} />}
          action={
            <button type="button" className={BTN_PRIMARY} onClick={openCreate}>
              <Plus size={15} /> Nueva plantilla
            </button>
          }
        />
      )}

      {items.length > 0 && (
        <section className="card overflow-x-auto">
          <table className="w-full text-left">
            <thead className="border-b border-line bg-app/60">
              <tr className="text-[10px] font-semibold uppercase tracking-[0.1em] text-muted">
                <th className="px-5 py-3">Evento</th>
                <th className="px-4 py-3">Clave</th>
                <th className="px-4 py-3">Asunto</th>
                <th className="px-4 py-3">Última actualización</th>
                <th className="px-4 py-3">Personalizada</th>
                <th className="px-4 py-3 text-right">Acciones</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-line">
              {items.map((plantilla) => {
                const personalizada =
                  plantilla.asunto !== plantilla.asunto_original ||
                  plantilla.cuerpo !== plantilla.cuerpo_original;
                return (
                  <tr key={plantilla.id} className="hover:bg-app/50">
                    <td className="px-5 py-3 text-sm font-semibold text-ink">
                      {CLAVE_PLANTILLA_LABELS[plantilla.clave] ?? plantilla.clave}
                    </td>
                    <td className="px-4 py-3 font-mono text-xs text-navy-900">{plantilla.clave}</td>
                    <td
                      className="max-w-72 truncate px-4 py-3 text-xs text-muted"
                      title={plantilla.asunto}
                    >
                      {plantilla.asunto}
                    </td>
                    <td className="px-4 py-3 text-xs text-muted">
                      {plantilla.updated_at ? formatDateTime(plantilla.updated_at) : "—"}
                    </td>
                    <td className="px-4 py-3">
                      <Badge
                        className={
                          personalizada
                            ? "bg-amber-50 text-amber-800 ring-amber-200"
                            : "bg-slate-100 text-slate-600 ring-slate-200"
                        }
                      >
                        {personalizada ? "Personalizada" : "Original"}
                      </Badge>
                    </td>
                    <td className="px-4 py-3">
                      <div className="flex justify-end gap-1">
                        <button
                          type="button"
                          className={BTN_GHOST}
                          onClick={() => setPreview(plantilla)}
                        >
                          <Eye size={14} /> Ver
                        </button>
                        <button
                          type="button"
                          className={BTN_GHOST}
                          onClick={() => openEdit(plantilla)}
                        >
                          <Pencil size={14} /> Editar
                        </button>
                      </div>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </section>
      )}

      <Modal
        open={editorOpen}
        onClose={() => setEditorOpen(false)}
        title={editing ? "Editar plantilla" : "Nueva plantilla"}
        description="La clave identifica el correo automático y no se puede cambiar después de crearla."
        wide
      >
        <form className="grid gap-3" onSubmit={submit}>
          <FormField
            label="Evento"
            required
            hint={editing ? "La clave no se puede cambiar" : undefined}
          >
            <select
              value={form.clave}
              disabled={editing !== null}
              onChange={(event) => setForm({ ...form, clave: event.target.value })}
              className={INPUT_CLASS}
            >
              <option value="">Selecciona un evento</option>
              {(editing ? CLAVES_PLANTILLA : availableKeys).map((clave) => (
                <option key={clave} value={clave}>
                  {CLAVE_PLANTILLA_LABELS[clave] ?? clave}
                </option>
              ))}
            </select>
          </FormField>
          <FormField label="Asunto" required hint="Máximo 150 caracteres">
            <input
              value={form.asunto}
              maxLength={150}
              onChange={(event) => setForm({ ...form, asunto: event.target.value })}
              className={INPUT_CLASS}
            />
          </FormField>
          <FormField
            label="Cuerpo"
            required
            hint="Máximo 2,000 caracteres. Puedes usar marcadores como {nombre}, {tarea} o {fecha}."
          >
            <textarea
              value={form.cuerpo}
              rows={10}
              maxLength={2000}
              onChange={(event) => setForm({ ...form, cuerpo: event.target.value })}
              className={`${INPUT_CLASS} font-mono text-xs`}
            />
          </FormField>
          {editing && (
            <div className="flex flex-wrap items-center justify-between gap-2 rounded-lg bg-app/60 p-3">
              <p className="text-xs text-muted">
                Texto original del sistema; puedes restaurarlo si lo personalizaste.
              </p>
              <button type="button" className={BTN_GHOST} onClick={restoreOriginal}>
                <RotateCcw size={14} /> Restaurar original
              </button>
            </div>
          )}
          <div className="flex justify-end gap-2">
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
                !form.clave ||
                form.asunto.trim().length === 0 ||
                form.cuerpo.trim().length === 0
              }
            >
              {saveMutation.isPending
                ? "Guardando…"
                : editing
                  ? "Guardar cambios"
                  : "Crear plantilla"}
            </button>
          </div>
        </form>
      </Modal>

      <Modal
        open={preview !== null}
        onClose={() => setPreview(null)}
        title={
          preview
            ? (CLAVE_PLANTILLA_LABELS[preview.clave] ?? preview.clave)
            : "Plantilla"
        }
        description={preview ? preview.clave : undefined}
        wide
        footer={
          preview ? (
            <>
              <button type="button" className={BTN_SECONDARY} onClick={() => setPreview(null)}>
                Cerrar
              </button>
              <button
                type="button"
                className={BTN_PRIMARY}
                onClick={() => {
                  setPreview(null);
                  openEdit(preview);
                }}
              >
                <Pencil size={15} /> Editar
              </button>
            </>
          ) : undefined
        }
      >
        {preview && (
          <div className="flex flex-col gap-3 text-sm">
            <div>
              <p className="text-[11px] font-semibold uppercase tracking-wide text-muted">Asunto</p>
              <p className="mt-1 font-semibold text-ink">{preview.asunto}</p>
            </div>
            <div>
              <p className="text-[11px] font-semibold uppercase tracking-wide text-muted">Cuerpo</p>
              <p className="mt-1 whitespace-pre-wrap rounded-lg bg-app/60 p-3 font-mono text-xs text-ink">
                {preview.cuerpo}
              </p>
            </div>
            {preview.cuerpo_original !== preview.cuerpo && (
              <div>
                <p className="text-[11px] font-semibold uppercase tracking-wide text-muted">
                  Cuerpo original
                </p>
                <p className="mt-1 whitespace-pre-wrap rounded-lg bg-app/40 p-3 font-mono text-xs text-muted">
                  {preview.cuerpo_original}
                </p>
              </div>
            )}
          </div>
        )}
      </Modal>
    </div>
  );
}
