import { REGIMENES_POR_CLAVE } from "./constants";

const AVATAR_TONES = [
  "bg-navy-900 text-white",
  "bg-gold-300 text-navy-900",
  "bg-[#e8eaf2] text-navy-800",
  "bg-[#374151] text-white",
  "bg-[#f1e6c8] text-[#6b5a00]",
] as const;

export function initials(name: string): string {
  const parts = name
    .replace(/\b(lic|dr|dra|ing|c\.?p|mtro|mtra|sr|sra)\.?/gi, " ")
    .replace(/\b(s\.?\s*a\.?\s*de\s*c\.?\s*v\.?|s\.?\s*a\.?\s*b\.?\s*de\s*c\.?\s*v\.?|s\.?\s*a\.?|s\.?\s*c\.?)\b/gi, " ")
    .replace(/\b(de|del|la|las|los|y)\b/gi, " ")
    .replace(/[.,]/g, " ")
    .split(/\s+/)
    .filter((part) => part.length > 1);

  const first = parts[0]?.[0] ?? "";
  const second = parts.length > 1 ? parts[parts.length - 1][0] : "";
  return `${first}${second}`.toUpperCase() || "?";
}

export function avatarTone(seed: string): string {
  let hash = 0;
  for (let i = 0; i < seed.length; i += 1) {
    hash = (hash * 31 + seed.charCodeAt(i)) % 997;
  }
  return AVATAR_TONES[hash % AVATAR_TONES.length];
}

export function formatHours(value: number | null | undefined): string {
  if (value === null || value === undefined) return "—";
  return value.toLocaleString("es-MX", {
    minimumFractionDigits: Number.isInteger(value) ? 0 : 1,
    maximumFractionDigits: 1,
  });
}

export function formatNumber(value: number | null | undefined): string {
  if (value === null || value === undefined) return "—";
  return value.toLocaleString("es-MX");
}

export function regimenName(clave: string): string {
  return REGIMENES_POR_CLAVE.get(clave)?.nombre ?? `Régimen ${clave}`;
}

export function regimenDescription(clave: string): string {
  return REGIMENES_POR_CLAVE.get(clave)?.descripcion ?? "Régimen registrado en el expediente.";
}

export function fullAddress(cliente: {
  calle?: string;
  no_exterior?: string;
  no_interior?: string | null;
  colonia?: string;
  ciudad?: string;
  estado?: string;
  codigo_postal?: string;
}): string | null {
  if (!cliente.calle && !cliente.colonia && !cliente.ciudad) return null;
  const line1 = [cliente.calle, cliente.no_exterior && `#${cliente.no_exterior}`, cliente.no_interior && `Int. ${cliente.no_interior}`]
    .filter(Boolean)
    .join(" ");
  const line2 = [cliente.colonia, cliente.ciudad, cliente.estado].filter(Boolean).join(", ");
  return [line1, line2, cliente.codigo_postal && `C.P. ${cliente.codigo_postal}`].filter(Boolean).join(" · ");
}

export function downloadCsv(filename: string, rows: (string | number | null | undefined)[][]): void {
  const body = rows
    .map((row) =>
      row
        .map((cell) => {
          const value = cell === null || cell === undefined ? "" : String(cell);
          return `"${value.replace(/"/g, '""')}"`;
        })
        .join(","),
    )
    .join("\r\n");

  // BOM para que Excel respete los acentos.
  const blob = new Blob([`\uFEFF${body}`], { type: "text/csv;charset=utf-8;" });
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement("a");
  anchor.href = url;
  anchor.download = filename;
  document.body.appendChild(anchor);
  anchor.click();
  anchor.remove();
  URL.revokeObjectURL(url);
}
