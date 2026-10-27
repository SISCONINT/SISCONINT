import { ChevronLeft, ChevronRight } from "lucide-react";
import clsx from "clsx";

function visiblePages(current: number, total: number): (number | "gap")[] {
  if (total <= 6) return Array.from({ length: total }, (_, i) => i + 1);

  const pages = new Set<number>([1, total, current - 1, current, current + 1]);
  const sorted = [...pages].filter((page) => page >= 1 && page <= total).sort((a, b) => a - b);
  const output: (number | "gap")[] = [];

  sorted.forEach((page, index) => {
    if (index > 0 && page - sorted[index - 1] > 1) output.push("gap");
    output.push(page);
  });

  return output;
}

interface Props {
  page: number;
  total: number;
  perPage: number;
  onPageChange: (page: number) => void;
}

export function Pagination({ page, total, perPage, onPageChange }: Props) {
  const pages = Math.max(1, Math.ceil(total / (perPage || 20)));
  const start = total === 0 ? 0 : (page - 1) * perPage + 1;
  const end = Math.min(page * perPage, total);

  return (
    <div className="flex flex-col gap-3 border-t border-line px-5 py-4 sm:flex-row sm:items-center sm:justify-between">
      <p className="text-xs text-muted">
        Mostrando <b className="text-ink">{start}</b>–<b className="text-ink">{end}</b> de{" "}
        <b className="text-ink">{total}</b> contribuyentes
      </p>

      <div className="flex items-center gap-1.5">
        <button
          type="button"
          onClick={() => onPageChange(page - 1)}
          disabled={page <= 1}
          className="grid size-8 place-items-center rounded-md border border-line text-ink transition hover:bg-app disabled:cursor-not-allowed disabled:opacity-40"
          aria-label="Página anterior"
        >
          <ChevronLeft size={15} />
        </button>

        {visiblePages(page, pages).map((item, index) =>
          item === "gap" ? (
            <span key={`gap-${index}`} className="px-1 text-xs text-muted">
              …
            </span>
          ) : (
            <button
              key={item}
              type="button"
              onClick={() => onPageChange(item)}
              aria-current={item === page ? "page" : undefined}
              className={clsx(
                "grid size-8 place-items-center rounded-md text-xs font-semibold transition",
                item === page
                  ? "bg-navy-900 text-white"
                  : "border border-line text-ink hover:bg-app",
              )}
            >
              {item}
            </button>
          ),
        )}

        <button
          type="button"
          onClick={() => onPageChange(page + 1)}
          disabled={page >= pages}
          className="grid size-8 place-items-center rounded-md border border-line text-ink transition hover:bg-app disabled:cursor-not-allowed disabled:opacity-40"
          aria-label="Página siguiente"
        >
          <ChevronRight size={15} />
        </button>
      </div>
    </div>
  );
}
