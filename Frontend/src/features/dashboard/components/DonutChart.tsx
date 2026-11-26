interface Slice {
  nombre: string;
  porcentaje: number;
  color: string;
}

interface Props {
  slices: Slice[];
  centerLabel: string;
  centerValue: string;
}

const R = 60;
const CIRC = 2 * Math.PI * R;

function withOffsets(slices: Slice[]): (Slice & { dash: number; offset: number })[] {
  let offset = 0;
  return slices.map((s) => {
    const dash = (s.porcentaje / 100) * CIRC;
    const withOffset = { ...s, dash, offset };
    offset += dash;
    return withOffset;
  });
}

const PALETTE = ["#0b1445", "#f5d547", "#1b2866", "#c9cfe6", "#6b7280", "#8a94c9", "#d9a441"];

export function DonutChart({ slices, centerLabel, centerValue }: Props) {
  const colored = slices.map((s, i) => ({ ...s, color: s.color || PALETTE[i % PALETTE.length] }));

  if (slices.length === 0) {
    return <p className="text-sm text-muted">Sin datos para este periodo.</p>;
  }

  return (
    <div className="flex flex-col items-center gap-5 sm:flex-row">
      <svg viewBox="0 0 160 160" className="size-36 shrink-0 -rotate-90">
        <circle cx="80" cy="80" r={R} fill="none" stroke="var(--color-field)" strokeWidth="20" />
        {withOffsets(colored).map((s) => (
          <circle
            key={s.nombre}
            cx="80"
            cy="80"
            r={R}
            fill="none"
            stroke={s.color}
            strokeWidth="20"
            strokeDasharray={`${s.dash} ${CIRC - s.dash}`}
            strokeDashoffset={-s.offset}
          />
        ))}
      </svg>
      <div className="w-full flex-1">
        <p className="mb-2 font-display text-xl font-bold text-ink">{centerValue}</p>
        <p className="mb-3 text-[11px] uppercase tracking-wide text-muted">{centerLabel}</p>
        <ul className="flex flex-col gap-1.5">
          {colored.map((s) => (
            <li key={s.nombre} className="flex items-center gap-2 text-[12px] text-ink">
              <span className="size-2.5 shrink-0 rounded-full" style={{ background: s.color }} />
              <span className="truncate">{s.nombre}</span>
              <span className="ml-auto shrink-0 font-semibold">{s.porcentaje}%</span>
            </li>
          ))}
        </ul>
      </div>
    </div>
  );
}
