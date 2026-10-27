import { initials } from "../utils/format";

export function Avatar({ nombre, size = 32 }: { nombre?: string | null; size?: number }) {
  return (
    <span
      className="grid shrink-0 place-items-center rounded-full bg-navy-900 font-semibold text-gold-500"
      style={{ width: size, height: size, fontSize: Math.max(10, size * 0.38) }}
    >
      {initials(nombre)}
    </span>
  );
}
