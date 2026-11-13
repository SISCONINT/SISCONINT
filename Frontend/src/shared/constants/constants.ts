/** Etiquetas y estilos compartidos por los módulos operativos. */

export const ESTADOS_TAREA = [
  "POR_HACER",
  "EN_PROGRESO",
  "EN_REVISION",
  "COMPLETADO",
] as const;

export type EstadoTarea = (typeof ESTADOS_TAREA)[number];

export const ESTADO_LABELS: Record<string, string> = {
  POR_HACER: "Por hacer",
  EN_PROGRESO: "En progreso",
  EN_REVISION: "En revisión",
  COMPLETADO: "Completado",
};

export const ESTADO_BADGE: Record<string, string> = {
  POR_HACER: "bg-slate-100 text-slate-700 ring-slate-200",
  EN_PROGRESO: "bg-sky-50 text-sky-700 ring-sky-200",
  EN_REVISION: "bg-amber-50 text-amber-800 ring-amber-200",
  COMPLETADO: "bg-emerald-50 text-emerald-700 ring-emerald-200",
};

export const PRIORIDADES = ["BAJA", "MEDIA", "ALTA"] as const;
export type Prioridad = (typeof PRIORIDADES)[number];

export const PRIORIDAD_LABELS: Record<string, string> = {
  BAJA: "Baja",
  MEDIA: "Media",
  ALTA: "Alta",
};

export const PRIORIDAD_BADGE: Record<string, string> = {
  BAJA: "bg-slate-100 text-slate-700 ring-slate-200",
  MEDIA: "bg-amber-50 text-amber-800 ring-amber-200",
  ALTA: "bg-rose-50 text-rose-700 ring-rose-200",
};

export const SEMAFORO_LABELS: Record<string, string> = {
  VERDE: "Verde",
  AMARILLO: "Amarillo",
  ROJO: "Rojo",
  GRIS: "Gris",
};

export const SEMAFORO_BADGE: Record<string, string> = {
  VERDE: "bg-emerald-50 text-emerald-700 ring-emerald-200",
  AMARILLO: "bg-amber-50 text-amber-800 ring-amber-200",
  ROJO: "bg-rose-50 text-rose-700 ring-rose-200",
  GRIS: "bg-slate-100 text-slate-600 ring-slate-200",
};

export const PERIODOS = [
  { value: "HOY", label: "Hoy" },
  { value: "SEMANA", label: "Esta semana" },
  { value: "MES_ACTUAL", label: "Mes actual" },
  { value: "MES_ANTERIOR", label: "Mes anterior" },
  { value: "PERSONALIZADO", label: "Rango personalizado" },
] as const;

export const PERIODICIDADES = [
  "SEMANAL",
  "QUINCENAL",
  "MENSUAL",
  "BIMESTRAL",
  "TRIMESTRAL",
  "SEMESTRAL",
  "ANUAL",
] as const;

export type Periodicidad = (typeof PERIODICIDADES)[number];

export const PERIODICIDAD_LABELS: Record<string, string> = {
  SEMANAL: "Semanal",
  QUINCENAL: "Quincenal",
  MENSUAL: "Mensual",
  BIMESTRAL: "Bimestral",
  TRIMESTRAL: "Trimestral",
  SEMESTRAL: "Semestral",
  ANUAL: "Anual",
};

export const TIPOS_MINUTA = ["CLIENTE", "PERSONAL"] as const;

export const TIPO_MINUTA_LABELS: Record<string, string> = {
  CLIENTE: "De cliente",
  PERSONAL: "Personal",
};

export const NIVELES_TARIFA = ["JUNIOR", "SENIOR", "ADMIN"] as const;

export const NIVEL_TARIFA_LABELS: Record<string, string> = {
  JUNIOR: "Junior",
  SENIOR: "Senior",
  ADMIN: "Admin",
};

export const CLAVES_PLANTILLA = ["ASIGNACION", "VENCIMIENTO", "COMPLETADA"] as const;

export const CLAVE_PLANTILLA_LABELS: Record<string, string> = {
  ASIGNACION: "Asignación de tarea",
  VENCIMIENTO: "Vencimiento de tarea",
  COMPLETADA: "Tarea completada",
};


export const BTN_PRIMARY =
  "inline-flex items-center justify-center gap-2 rounded-lg bg-gold-300 px-4 py-2.5 text-sm font-semibold text-navy-900 shadow-[0_6px_14px_rgb(245_213_71/35%)] transition hover:brightness-95 disabled:cursor-not-allowed disabled:opacity-60";

export const BTN_SECONDARY =
  "inline-flex items-center justify-center gap-2 rounded-lg border border-line bg-surface px-4 py-2.5 text-sm font-semibold text-ink transition hover:border-navy-900/20 hover:bg-app disabled:cursor-not-allowed disabled:opacity-60";

export const BTN_GHOST =
  "inline-flex items-center justify-center gap-2 rounded-lg px-3 py-2 text-xs font-semibold text-navy-800 transition hover:bg-navy-900/5 disabled:cursor-not-allowed disabled:opacity-60";

export const BTN_DANGER =
  "inline-flex items-center justify-center gap-2 rounded-lg border border-rose-200 bg-rose-50 px-3 py-2 text-xs font-semibold text-rose-700 transition hover:bg-rose-100 disabled:cursor-not-allowed disabled:opacity-60";

export const INPUT_CLASS =
  "w-full rounded-lg border border-line bg-surface px-3 py-2 text-sm text-ink outline-none transition placeholder:text-muted/70 focus:border-navy-900/30 disabled:bg-app";

export const LABEL_CLASS = "text-[11px] font-semibold uppercase tracking-wide text-muted";
