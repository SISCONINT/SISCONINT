/** RG-04: las fechas se muestran DD/MM/AAAA en toda la interfaz. */
export function formatDate(value?: string | Date | null): string {
  if (!value) return "—";
  const d = typeof value === "string" ? new Date(value) : value;
  if (Number.isNaN(d.getTime())) return "—";
  const dd = String(d.getUTCDate()).padStart(2, "0");
  const mm = String(d.getUTCMonth() + 1).padStart(2, "0");
  const yyyy = d.getUTCFullYear();
  return `${dd}/${mm}/${yyyy}`;
}

export function formatDateTime(value?: string | Date | null): string {
  if (!value) return "—";
  const d = typeof value === "string" ? new Date(value) : value;
  if (Number.isNaN(d.getTime())) return "—";
  const dd = String(d.getDate()).padStart(2, "0");
  const mm = String(d.getMonth() + 1).padStart(2, "0");
  const yyyy = d.getFullYear();
  const hh = String(d.getHours()).padStart(2, "0");
  const min = String(d.getMinutes()).padStart(2, "0");
  return `${dd}/${mm}/${yyyy} ${hh}:${min} h`;
}

export function formatHours(value?: number | null): string {
  if (value === null || value === undefined) return "—";
  return `${value.toFixed(1)} hrs`;
}

export function initials(nombre?: string | null): string {
  if (!nombre) return "—";
  const parts = nombre.trim().split(/\s+/).filter(Boolean);
  if (parts.length === 0) return "—";
  if (parts.length === 1) return parts[0].slice(0, 2).toUpperCase();
  return (parts[0][0] + parts[1][0]).toUpperCase();
}

const ESTADO_LABEL: Record<string, string> = {
  POR_HACER: "Por hacer",
  EN_PROGRESO: "En progreso",
  EN_REVISION: "En revisión",
  COMPLETADO: "Completado",
};

export function estadoLabel(estado: string): string {
  return ESTADO_LABEL[estado] ?? estado;
}

/** Normaliza un objeto de filtros para usarlo como query string, quitando vacíos. */
export function toQueryParams(filters: object): Record<string, string> {
  const out: Record<string, string> = {};
  for (const [key, value] of Object.entries(filters as Record<string, unknown>)) {
    if (value === undefined || value === null || value === "") continue;
    out[key] = String(value);
  }
  return out;
}
