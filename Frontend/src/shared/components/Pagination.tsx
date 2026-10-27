import { ChevronLeft, ChevronRight } from "lucide-react";

interface Props {
  page: number;
  perPage: number;
  total: number;
  onChange: (page: number) => void;
}

export function Pagination({ page, perPage, total, onChange }: Props) {
  const totalPages = Math.max(1, Math.ceil(total / perPage));
  const from = total === 0 ? 0 : (page - 1) * perPage + 1;
  const to = Math.min(page * perPage, total);

  const btn =
    "grid size-8 place-items-center rounded-md bg-field text-ink transition hover:brightness-95 disabled:cursor-not-allowed disabled:opacity-40";

  return (
    <div className="flex flex-wrap items-center justify-between gap-3 px-4 py-3 text-xs text-muted">
      <span>Mostrando {from} a {to} de {total} resultados</span>
      <div className="flex items-center gap-2">
        <button type="button" className={btn} disabled={page <= 1} onClick={() => onChange(page - 1)} aria-label="Página anterior">
          <ChevronLeft size={16} />
        </button>
        <span>Página {page} de {totalPages}</span>
        <button type="button" className={btn} disabled={page >= totalPages} onClick={() => onChange(page + 1)} aria-label="Página siguiente">
          <ChevronRight size={16} />
        </button>
      </div>
    </div>
  );
}