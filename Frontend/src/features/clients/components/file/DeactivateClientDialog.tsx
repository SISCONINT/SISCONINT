import { useState } from "react";
import { ShieldOff, X } from "lucide-react";
import { ApiError } from "@/shared/api/types";
import { useDeactivateClient } from "../../api/useClients";
import { BTN_SECONDARY } from "../../constants";

interface Props {
  clientId: number;
  nombre: string;
  open: boolean;
  onClose: () => void;
}

export function DeactivateClientDialog({ clientId, nombre, open, onClose }: Props) {
  const [motivo, setMotivo] = useState("");
  const { mutate, isPending, error, reset } = useDeactivateClient(clientId);

  if (!open) return null;

  const handleClose = () => {
    setMotivo("");
    reset();
    onClose();
  };

  return (
    <div className="fixed inset-0 z-50 grid place-items-center bg-navy-950/40 px-4" role="dialog" aria-modal="true">
      <div className="w-full max-w-md rounded-2xl bg-surface p-5 shadow-[0_20px_50px_rgb(16_24_40/25%)]">
        <div className="mb-3 flex items-start justify-between gap-3">
          <div className="flex items-start gap-2.5">
            <span className="grid size-9 shrink-0 place-items-center rounded-full bg-red-50 text-danger">
              <ShieldOff size={18} />
            </span>
            <div>
              <h2 className="font-semibold text-ink">Dar de baja a {nombre}</h2>
              <p className="mt-1 text-sm text-muted">
                HU_15: el cliente deja de atenderse, pero su historial de tareas y tiempos se conserva.
              </p>
            </div>
          </div>
          <button type="button" onClick={handleClose} className="text-muted hover:text-ink" aria-label="Cerrar">
            <X size={18} />
          </button>
        </div>

        <label className="mb-1.5 block text-sm font-semibold text-ink" htmlFor="motivo-baja">
          Motivo de la baja <span className="text-danger">*</span>
        </label>
        <textarea
          id="motivo-baja"
          rows={3}
          value={motivo}
          onChange={(e) => setMotivo(e.target.value)}
          maxLength={300}
          className="w-full rounded-lg bg-field px-3.5 py-3 text-sm text-ink outline-none ring-1 ring-transparent focus:ring-gold-500"
          placeholder="Ej. Cliente dio por terminada la relación comercial."
        />

        {error && (
          <p className="mt-2 text-sm text-danger">
            {error instanceof ApiError ? error.message : "No se pudo dar de baja al cliente."}
          </p>
        )}

        <div className="mt-4 flex justify-end gap-2">
          <button type="button" onClick={handleClose} className={BTN_SECONDARY}>
            Cancelar
          </button>
          <button
            type="button"
            onClick={() => mutate(motivo.trim(), { onSuccess: handleClose })}
            disabled={motivo.trim().length === 0 || isPending}
            className="rounded-lg bg-danger px-4 py-2 text-sm font-semibold text-white hover:brightness-95 disabled:opacity-60"
          >
            {isPending ? "Guardando…" : "Dar de baja"}
          </button>
        </div>
      </div>
    </div>
  );
}
