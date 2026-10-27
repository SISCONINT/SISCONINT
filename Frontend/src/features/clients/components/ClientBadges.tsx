import clsx from "clsx";
import { ESTATUS_BADGE, ESTATUS_DOT, ESTATUS_LABELS, TIPO_PERSONA_LABELS } from "../constants";
import type { EstatusCliente, TipoPersona } from "../types";

export function StatusBadge({ estatus, className }: { estatus: EstatusCliente; className?: string }) {
  return (
    <span
      className={clsx(
        "inline-flex items-center gap-1.5 rounded-full px-2.5 py-1 text-[11px] font-semibold ring-1 ring-inset",
        ESTATUS_BADGE[estatus],
        className,
      )}
    >
      <span className={clsx("size-1.5 rounded-full", ESTATUS_DOT[estatus])} />
      {ESTATUS_LABELS[estatus]}
    </span>
  );
}

export function TipoPersonaBadge({ tipo, className }: { tipo: TipoPersona; className?: string }) {
  return (
    <span
      className={clsx(
        "inline-flex items-center rounded bg-navy-900/[0.06] px-1.5 py-0.5 text-[10px] font-semibold uppercase tracking-wide text-navy-800",
        className,
      )}
    >
      {TIPO_PERSONA_LABELS[tipo]}
    </span>
  );
}
