import { useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import {
  CheckSquare,
  Clock,
  FileText,
  History,
  MessageSquare,
  Pencil,
  Trash2,
} from "lucide-react";
import { PageHeader } from "@/shared/components/PageHeader";
import { Avatar } from "@/shared/components/Avatar";
import { ConfirmDialog } from "@/shared/components/ConfirmDialog";
import { EstadoBadge, PrioridadBadge, SemaforoDot } from "@/shared/components/Badge";
import { estadoLabel, formatDate, formatDateTime } from "@/shared/utils/format";
import { ApiError } from "@/shared/api/types";
import { useDeleteTask, useMoveTask, useTask, useUpdateTask } from "../api/useTasks";
import { TaskForm } from "../components/TaskForm";
import { ESTADOS } from "../types";
import type { TareaFormValues } from "../types";

export function TaskDetailPage() {
  const { id } = useParams();
  const taskId = Number(id);
  const navigate = useNavigate();
  const [editing, setEditing] = useState(false);
  const [deleting, setDeleting] = useState(false);
  const [conflict, setConflict] = useState<string | null>(null);

  const { data: tarea, isLoading, isError } = useTask(taskId);
  const updateMutation = useUpdateTask(taskId);
  const moveMutation = useMoveTask(taskId);
  const deleteMutation = useDeleteTask();

  if (isLoading) return <p className="text-sm text-muted">Cargando tarea…</p>;
  if (isError || !tarea) return <p className="text-sm text-danger">No se encontró la tarea.</p>;

  const handleMove = (estado: string, confirmar = false) => {
    moveMutation.mutate(
      { estado, confirmar },
      {
        onError: (e) => {
          if (e instanceof ApiError && e.status === 409 && e.extra?.subtareas_pendientes) {
            setConflict(estado);
          }
        },
      },
    );
  };

  const toFormValues = (): Partial<TareaFormValues> => ({
    titulo: tarea.titulo,
    descripcion: tarea.descripcion ?? "",
    cliente_id: tarea.cliente_id,
    categoria_id: tarea.categoria_id,
    asignado_id: tarea.asignado_id,
    fecha_limite: tarea.fecha_limite,
    hora_limite: tarea.hora_limite ?? "23:59",
    prioridad: tarea.prioridad,
    horas_estimadas: tarea.horas_estimadas ? String(tarea.horas_estimadas) : "",
    notificar_cliente: tarea.notificar_cliente,
  });

  return (
    <div>
      <PageHeader
        title={tarea.titulo}
        crumbs={[
          { label: "Tablero Kanban", to: "/tablero" },
          { label: `Folio TP-${tarea.id}` },
        ]}
        actions={
          !editing && (
            <div className="flex gap-2">
              <button
                type="button"
                onClick={() => setEditing(true)}
                className="flex items-center gap-2 rounded-lg border border-line px-4 py-2.5 text-sm font-medium text-ink hover:bg-field"
              >
                <Pencil size={15} /> Editar
              </button>
              <button
                type="button"
                onClick={() => setDeleting(true)}
                className="flex items-center gap-2 rounded-lg bg-red-50 px-4 py-2.5 text-sm font-semibold text-danger hover:brightness-95"
              >
                <Trash2 size={15} /> Eliminar
              </button>
            </div>
          )
        }
      />

      <p className="mb-5 text-sm text-muted">
        TP-{tarea.id} · Creada el {formatDateTime(tarea.created_at)} por {tarea.creador_nombre ?? "—"} ·{" "}
        {tarea.cliente_nombre}
      </p>

      {editing ? (
        <div className="card p-5">
          <TaskForm
            defaultValues={toFormValues()}
            submitLabel="Guardar cambios"
            pending={updateMutation.isPending}
            serverError={updateMutation.error}
            onCancel={() => setEditing(false)}
            onSubmit={(values) => updateMutation.mutate(values, { onSuccess: () => setEditing(false) })}
          />
        </div>
      ) : (
        <div className="grid grid-cols-1 gap-5 lg:grid-cols-[1fr_320px]">
          <div className="flex flex-col gap-5">
            {tarea.descripcion && (
              <div className="card p-5">
                <h2 className="mb-2 flex items-center gap-2 font-semibold text-ink">
                  <FileText size={17} /> Descripción
                </h2>
                <p className="whitespace-pre-wrap text-sm text-ink/90">{tarea.descripcion}</p>
              </div>
            )}

            <div className="card p-5">
              <div className="mb-3 flex items-center justify-between">
                <h2 className="flex items-center gap-2 font-semibold text-ink">
                  <CheckSquare size={17} /> Subtareas
                </h2>
                <span className="text-sm font-semibold text-ink">
                  {tarea.subtareas.avance} · {tarea.subtareas.porcentaje}%
                </span>
              </div>
              <div className="mb-3 h-1.5 w-full overflow-hidden rounded-full bg-field">
                <div className="h-full bg-gold-500" style={{ width: `${tarea.subtareas.porcentaje}%` }} />
              </div>
              {tarea.subtareas.items.length === 0 ? (
                <p className="text-sm text-muted">Esta tarea no tiene subtareas.</p>
              ) : (
                <ul className="flex flex-col gap-2">
                  {tarea.subtareas.items.map((s) => (
                    <li key={s.id} className="flex items-start gap-2.5 rounded-lg bg-field/60 px-3 py-2.5">
                      <input type="checkbox" checked={s.completada} readOnly className="mt-0.5 size-4 accent-navy-900" />
                      <div>
                        <p className={s.completada ? "text-sm text-ink line-through" : "text-sm text-ink"}>{s.titulo}</p>
                        {s.completada && (
                          <p className="text-[12px] text-muted">
                            Completada por {s.completada_por_nombre ?? "—"} · {formatDateTime(s.completada_en)}
                          </p>
                        )}
                      </div>
                    </li>
                  ))}
                </ul>
              )}
            </div>

            <div className="card p-5">
              <h2 className="mb-1 flex items-center gap-2 font-semibold text-ink">
                <Clock size={17} /> Tiempo registrado
              </h2>
              <p className="mb-3 text-sm text-muted">
                {tarea.tiempo.total_horas.toFixed(1)} hrs de {tarea.tiempo.horas_estimadas?.toFixed(1) ?? "—"} hrs estimadas
                {tarea.tiempo.porcentaje_registrado != null && ` · ${tarea.tiempo.porcentaje_registrado}% del presupuesto`}
              </p>
              {tarea.tiempo.por_colaborador.length === 0 ? (
                <p className="text-sm text-muted">Sin tiempo registrado todavía.</p>
              ) : (
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b border-line text-left text-[11px] font-semibold uppercase tracking-wide text-muted">
                      <th className="py-2">Colaborador</th>
                      <th className="py-2 text-right">Horas</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-line">
                    {tarea.tiempo.por_colaborador.map((c) => (
                      <tr key={c.colaborador_id}>
                        <td className="flex items-center gap-2 py-2">
                          <Avatar nombre={c.colaborador_nombre} size={24} /> {c.colaborador_nombre}
                        </td>
                        <td className="py-2 text-right font-medium text-ink">{c.horas.toFixed(1)} hrs</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              )}
            </div>

            <div className="card p-5">
              <h2 className="mb-1 flex items-center gap-2 font-semibold text-ink">
                <MessageSquare size={17} /> Comentarios
              </h2>
              <p className="mb-3 text-[12px] text-muted">{tarea.comentarios.length} aportación(es)</p>
              {tarea.comentarios.length === 0 ? (
                <p className="text-sm text-muted">Sin comentarios.</p>
              ) : (
                <ul className="flex flex-col gap-3">
                  {tarea.comentarios.map((c) => (
                    <li key={c.id} className="flex gap-2.5">
                      <Avatar nombre={c.autor_nombre} size={28} />
                      <div className="min-w-0 flex-1 rounded-lg bg-field/60 px-3 py-2.5">
                        <div className="flex items-center justify-between gap-2">
                          <p className="text-sm font-semibold text-ink">{c.autor_nombre}</p>
                          <p className="text-[11px] text-muted">
                            {formatDateTime(c.created_at)}
                            {c.editado && " · editado"}
                          </p>
                        </div>
                        <p className="mt-1 text-sm text-ink/90">{c.texto}</p>
                      </div>
                    </li>
                  ))}
                </ul>
              )}
            </div>

            <div className="card p-5">
              <h2 className="mb-3 flex items-center gap-2 font-semibold text-ink">
                <History size={17} /> Historial de estados
              </h2>
              {tarea.historial_estados.length === 0 ? (
                <p className="text-sm text-muted">Sin movimientos registrados.</p>
              ) : (
                <ul className="flex flex-col gap-3 border-l border-line pl-4">
                  {tarea.historial_estados.map((h) => (
                    <li key={h.id} className="relative">
                      <span className="absolute -left-[21px] top-1 size-2.5 rounded-full bg-gold-500" />
                      <p className="text-sm text-ink">
                        <b>{h.usuario_nombre ?? "Sistema"}</b> movió la tarea
                        {h.estado_anterior ? ` de "${estadoLabel(h.estado_anterior)}"` : ""} a "{estadoLabel(h.estado_nuevo)}"
                      </p>
                      <p className="text-[12px] text-muted">{formatDateTime(h.created_at)}</p>
                    </li>
                  ))}
                </ul>
              )}
            </div>
          </div>

          <div className="flex flex-col gap-5">
            <div className="card p-5">
              <h3 className="mb-2 text-[11px] font-semibold uppercase tracking-wide text-muted">Estado</h3>
              <select
                value={tarea.estado}
                onChange={(e) => handleMove(e.target.value)}
                disabled={moveMutation.isPending}
                className="mb-3 w-full rounded-lg bg-field py-2.5 px-3 text-sm font-semibold text-ink outline-none"
              >
                {ESTADOS.map((e) => (
                  <option key={e} value={e}>
                    {estadoLabel(e)}
                  </option>
                ))}
              </select>
              <div className="flex items-center gap-2 border-t border-line pt-3">
                <SemaforoDot semaforo={tarea.semaforo} withLabel />
              </div>
              <p className="mt-1 text-sm text-ink">
                Vence el <b>{formatDate(tarea.fecha_limite)}</b> {tarea.hora_limite && `· ${tarea.hora_limite} h`}
              </p>
              <p className="text-[12px] text-muted">
                {tarea.dias_restantes >= 0 ? `${tarea.dias_restantes} día(s) restantes` : "Vencida"}
              </p>
            </div>

            <div className="card p-5">
              <h3 className="mb-3 text-[11px] font-semibold uppercase tracking-wide text-muted">Expediente y atributos</h3>
              <dl className="flex flex-col gap-3 text-sm">
                <div>
                  <dt className="text-muted">Cliente</dt>
                  <dd className="font-medium text-ink">{tarea.cliente_nombre}</dd>
                </div>
                <div>
                  <dt className="text-muted">Servicio y categoría</dt>
                  <dd className="font-medium text-ink">
                    {tarea.categoria_padre_nombre ? `${tarea.categoria_padre_nombre} · ` : ""}
                    {tarea.categoria_nombre}
                  </dd>
                </div>
                <div>
                  <dt className="text-muted">Prioridad</dt>
                  <dd>
                    <PrioridadBadge prioridad={tarea.prioridad} />
                  </dd>
                </div>
                <div>
                  <dt className="text-muted">Responsable asignado</dt>
                  <dd className="flex items-center gap-2 font-medium text-ink">
                    <Avatar nombre={tarea.asignado_nombre} size={24} /> {tarea.asignado_nombre}
                  </dd>
                </div>
                <div>
                  <dt className="text-muted">Estado actual</dt>
                  <dd>
                    <EstadoBadge estado={tarea.estado} />
                  </dd>
                </div>
              </dl>
            </div>
          </div>
        </div>
      )}

      <ConfirmDialog
        open={!!conflict}
        title="La tarea tiene subtareas pendientes"
        description="¿Confirmas mover esta tarea a Completado de todas formas? (RG-14)"
        confirmLabel="Mover de todas formas"
        pending={moveMutation.isPending}
        onConfirm={() => conflict && handleMove(conflict, true)}
        onCancel={() => setConflict(null)}
      />

      <ConfirmDialog
        open={deleting}
        title={`Eliminar "${tarea.titulo}"`}
        description="Esta acción elimina también sus subtareas y comentarios (RG-03)."
        confirmLabel="Eliminar"
        danger
        pending={deleteMutation.isPending}
        onConfirm={() => deleteMutation.mutate(taskId, { onSuccess: () => navigate("/tareas") })}
        onCancel={() => setDeleting(false)}
      />
    </div>
  );
}
