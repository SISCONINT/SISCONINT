import { FlaskConical } from "lucide-react";

/** Marca los widgets que todavía usan datos de ejemplo (sin API de horas/costos aún). */
export function SampleBadge() {
  return (
    <span className="inline-flex items-center gap-1 rounded-full bg-field px-2 py-0.5 text-[10px] font-semibold text-muted" title="Este bloque usa datos de ejemplo; aún no hay API de horas/costos">
      <FlaskConical size={11} /> Ejemplo
    </span>
  );
}
