import { ApiError } from "@/shared/api/types";

/** Une clases condicionales sin dependencias extra. */
export function cn(...values: Array<string | false | null | undefined>): string {
  return values.filter(Boolean).join(" ");
}

/** Convierte una fecha ISO (AAAA-MM-DD o timestamp) al formato DD/MM/AAAA. */
export function formatDate(value?: string | null): string {
  if (!value) return "—";
  const iso = value.slice(0, 10);
  const [year, month, day] = iso.split("-");
  if (!year || !month || !day) return value;
  return `${day}/${month}/${year}`;
}

/** Fecha y hora legibles (DD/MM/AAAA HH:MM). */
export function formatDateTime(value?: string | null): string {
  if (!value) return "—";
  const date = formatDate(value);
  const time = new Date(value).toLocaleTimeString("es-MX", {
    hour: "2-digit",
    minute: "2-digit",
  });
  return `${date} ${time}`;
}

/** Fecha local en formato AAAA-MM-DD (sin desfase por zona horaria). */
export function todayISO(): string {
  return toISO(new Date());
}

export function toISO(date: Date): string {
  const year = date.getFullYear();
  const month = String(date.getMonth() + 1).padStart(2, "0");
  const day = String(date.getDate()).padStart(2, "0");
  return `${year}-${month}-${day}`;
}

export function addDaysISO(iso: string, days: number): string {
  const [year, month, day] = iso.split("-").map(Number);
  const date = new Date(year, (month ?? 1) - 1, day ?? 1);
  date.setDate(date.getDate() + days);
  return toISO(date);
}

/** Primer y último día del mes que contiene la fecha indicada. */
export function monthBounds(anchor: string = todayISO()): {
  desde: string;
  hasta: string;
} {
  const [year, month] = anchor.split("-").map(Number);
  const first = new Date(year, (month ?? 1) - 1, 1);
  const last = new Date(year, month ?? 1, 0);
  return { desde: toISO(first), hasta: toISO(last) };
}

export function formatMinutes(minutes?: number | null): string {
  const total = Math.max(0, Math.round(minutes ?? 0));
  const hours = Math.floor(total / 60);
  const rest = total % 60;
  if (hours === 0) return `${rest} min`;
  return rest === 0 ? `${hours} h` : `${hours} h ${rest} min`;
}

export function formatHours(minutes?: number | null): string {
  return `${((minutes ?? 0) / 60).toFixed(1)} h`;
}

export function formatMoney(value?: number | null, currency = "MXN"): string {
  if (value === null || value === undefined) return "—";
  return new Intl.NumberFormat("es-MX", {
    style: "currency",
    currency,
    maximumFractionDigits: 2,
  }).format(value);
}

export function initials(name?: string | null): string {
  if (!name) return "?";
  return name
    .split(/\s+/)
    .filter(Boolean)
    .slice(0, 2)
    .map((part) => part[0]?.toUpperCase() ?? "")
    .join("");
}

export function getErrorMessage(error: unknown): string {
  if (error instanceof ApiError) {
    const fieldMessage = error.fields
      ? Object.values(error.fields).flat().find(Boolean)
      : undefined;
    return fieldMessage ?? error.message;
  }
  if (error instanceof Error) return error.message;
  return "Ocurrió un error inesperado";
}

/** Descarga un CSV compatible con Excel (incluye BOM UTF-8). */
export function downloadCsv(
  filename: string,
  rows: Array<Record<string, unknown>>,
  headers?: Record<string, string>,
): void {
  if (rows.length === 0) return;

  const columns = Object.keys(rows[0]);
  const escape = (value: unknown) => {
    const text = value === null || value === undefined ? "" : String(value);
    return `"${text.replace(/"/g, '""')}"`;
  };

  const head = headers
    ? columns.map((column) => escape(headers[column] ?? column))
    : columns.map(escape);
  const body = rows.map((row) => columns.map((column) => escape(row[column])));

  const csv = `\uFEFF${[head, ...body].map((line) => line.join(",")).join("\r\n")}`;
  const blob = new Blob([csv], { type: "text/csv;charset=utf-8;" });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = filename;
  link.click();
  URL.revokeObjectURL(url);
}

/** Convierte un valor de <input type="date"> a ISO sin zonas horarias. */
export function inputDateValue(value?: string | null): string {
  return value ? value.slice(0, 10) : "";
}
