import { useState } from "react";
import { TriangleAlert, X } from "lucide-react";
import { ROLE_LABELS } from "@/shared/constants/roles";
import { useDeactivationImpact, useDeactivateUser } from "../api/useUsers";

interface Props {
  userId: number;
  nombre: string;
  open: boolean;
  onClose: () => void;
  onDeactivated: () => void;
}

export function DeactivateDialog({ userId, nombre, open, onClose, onDeactivated }: Props) {
  const [reasignarA, setReasignarA] = useState<number | "">("");
  const { data: impact, isLoading } = useDeactivationImpact(open ? userId : undefined);
  const { mutate, isPending, error } = useDeactivateUser(userId);

  if (!open) return null;

  const requiere = impact?.requiere_reasignacion ?? false;
  const canConfirm = !requiere || reasignarA !== "";

  const handleConfirm = () => {
    mutate(reasignarA === "" ? null : reasignarA, {
      onSuccess: () => {
        onDeactivated();
        onClose();
      },
    });
  };

  return (
    <div className="fixed inset-0 z-50 grid place-items-center bg-navy-950/40 px-4" role="dialog" aria-modal="true">
      <div className="w-full max-w-md rounded-2xl bg-surface p-5 shadow-[0_20px_50px_rgb(16_24_40/25%)]">
        <div className="mb-3 flex items-start justify-between gap-3">
          <div className="flex items-start gap-2.5">
            <span className="grid size-9 shrink-0 place-items-center rounded-full bg-amber-50 text-amber-700">
              <TriangleAlert size={18} />
            </span>
            <div>
              <h2 className="font-semibold text-ink">Desactivar a {nombre}</h2>
              <p className="mt-1 text-sm text-muted">HU_09: revisa el impacto antes de confirmar.</p>
            </div>
          </div>
          <button type="button" onClick={onClose} className="text-muted hover:text-ink" aria-label="Cerrar">
            <X size={18} />
          </button>
        </div>

        {isLoading ? (
          <p className="py-4 text-sm text-muted">Calculando impacto…</p>
        ) : impact ? (
          <div className="space-y-3">
            <div className="grid grid-cols-2 gap-3 rounded-lg bg-field p-3 text-sm">
              <div>
                <p className="text-muted">Clientes asignados</p>
                <p className="font-semibold text-ink">{impact.clientes_asignados}</p>
              </div>
              <div>
                <p className="text-muted">Tareas abiertas</p>
                <p className="font-semibold text-ink">{impact.tareas_abiertas}</p>
              </div>
            </div>

            {requiere && (
              <div>
                <label className="mb-1.5 block text-sm font-semibold text-ink">
                  Reasignar clientes y tareas a <span className="text-danger">*</span>
                </label>
                <select
                  value={reasignarA}
                  onChange={(e) => setReasignarA(e.target.value ? Number(e.target.value) : "")}
                  className="w-full rounded-lg bg-field py-2.5 px-3 text-sm text-ink outline-none ring-1 ring-transparent focus:ring-gold-500"
                >
                  <option value="">Selecciona un colaborador…</option>
                  {impact.destinos.map((d) => (
                    <option key={d.id} value={d.id}>
                      {d.nombre_completo} ({ROLE_LABELS[d.rol]})
                    </option>
                  ))}
                </select>
                {impact.destinos.length === 0 && (
                  <p className="mt-1 text-xs text-danger">No hay otro colaborador activo disponible para reasignar.</p>
                )}
              </div>
            )}

            {error && <p className="text-sm text-danger">No se pudo desactivar. Intenta de nuevo.</p>}
          </div>
        ) : null}

        <div className="mt-5 flex justify-end gap-2">
          <button type="button" onClick={onClose} className="rounded-lg border border-line px-4 py-2 text-sm font-medium text-ink hover:bg-field">
            Cancelar
          </button>
          <button
            type="button"
            onClick={handleConfirm}
            disabled={!canConfirm || isPending || isLoading}
            className="rounded-lg bg-danger px-4 py-2 text-sm font-semibold text-white hover:brightness-95 disabled:opacity-60"
          >
            {isPending ? "Desactivando…" : "Desactivar"}
          </button>
        </div>
      </div>
    </div>
  );
}
