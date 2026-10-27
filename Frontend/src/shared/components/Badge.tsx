import clsx from "clsx";
import type { ReactNode } from "react";
import { estadoLabel } from "../utils/format";

type Tone = "neutral" | "success" | "warning" | "danger" | "info" | "gold";

const TONE_CLASS: Record<Tone, string> = {
  neutral: "bg-field text-muted",
  success: "bg-emerald-50 text-emerald-700",
  warning: "bg-amber-50 text-amber-700",
  danger: "bg-red-50 text-danger",
  info: "bg-navy-700/10 text-navy-700",
  gold: "bg-gold-300/40 text-gold-700",
};

export function Badge({ tone = "neutral", children }: { tone?: Tone; children: ReactNode }) {
  return (
    <span
      className={clsx(
        "inline-flex items-center gap-1 rounded-full px-2.5 py-1 text-[11px] font-semibold",
        TONE_CLASS[tone],
      )}
    >
      {children}
    </span>
  );
}

const ESTATUS_TONE: Record<string, Tone> = {
  ACTIVO: "success",
  INACTIVO: "neutral",
  PAUSADO: "warning",
  BAJA: "danger",
};

export function EstatusBadge({ estatus }: { estatus: string }) {
  return <Badge tone={ESTATUS_TONE[estatus] ?? "neutral"}>{estatus}</Badge>;
}

const PRIORIDAD_TONE: Record<string, Tone> = {
  ALTA: "danger",
  MEDIA: "warning",
  BAJA: "info",
};

const PRIORIDAD_LABEL: Record<string, string> = {
  ALTA: "Alta",
  MEDIA: "Media",
  BAJA: "Baja",
};

export function PrioridadBadge({ prioridad }: { prioridad: string }) {
  return <Badge tone={PRIORIDAD_TONE[prioridad] ?? "neutral"}>{PRIORIDAD_LABEL[prioridad] ?? prioridad}</Badge>;
}

const SEMAFORO_DOT: Record<string, string> = {
  VERDE: "bg-emerald-500",
  AMARILLO: "bg-amber-500",
  ROJO: "bg-red-600",
  GRIS: "bg-muted",
};

const SEMAFORO_LABEL: Record<string, string> = {
  VERDE: "En tiempo",
  AMARILLO: "Por vencer",
  ROJO: "Vencida",
  GRIS: "Completada",
};

export function SemaforoDot({ semaforo, withLabel }: { semaforo: string; withLabel?: boolean }) {
  return (
    <span className="inline-flex items-center gap-1.5 text-[12px] font-medium text-ink">
      <span className={clsx("size-2.5 shrink-0 rounded-full", SEMAFORO_DOT[semaforo] ?? "bg-muted")} />
      {withLabel && (SEMAFORO_LABEL[semaforo] ?? semaforo)}
    </span>
  );
}

const ESTADO_TONE: Record<string, Tone> = {
  POR_HACER: "neutral",
  EN_PROGRESO: "info",
  EN_REVISION: "warning",
  COMPLETADO: "success",
};

export function EstadoBadge({ estado }: { estado: string }) {
  return <Badge tone={ESTADO_TONE[estado] ?? "neutral"}>{estadoLabel(estado)}</Badge>;
}
