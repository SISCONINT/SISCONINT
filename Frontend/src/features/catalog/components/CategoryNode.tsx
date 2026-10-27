import { useState } from "react";
import { ChevronRight, FolderOpen, FolderClosed } from "lucide-react";
import clsx from "clsx";
import { Badge } from "@/shared/components/Badge";
import type { Categoria } from "../types";

export function CategoryNode({ categoria }: { categoria: Categoria }) {
  const [open, setOpen] = useState(true);
  const total = categoria.subcategorias.length;
  const activas = categoria.subcategorias.filter((s) => s.activa).length;

  return (
    <div className="border-b border-line last:border-0">
      <button
        type="button"
        onClick={() => setOpen((o) => !o)}
        className="flex w-full items-center gap-3 px-4 py-3.5 text-left hover:bg-field"
      >
        <ChevronRight size={16} className={clsx("shrink-0 text-muted transition-transform", open && "rotate-90")} />
        <span className="grid size-9 shrink-0 place-items-center rounded-lg bg-navy-900/5 text-navy-900">
          {open ? <FolderOpen size={17} /> : <FolderClosed size={17} />}
        </span>
        <div className="min-w-0 flex-1">
          <p className="truncate font-semibold text-ink">{categoria.nombre}</p>
          <p className="text-[12px] text-muted">
            {total} subcategoría{total === 1 ? "" : "s"} · {activas} activa{activas === 1 ? "" : "s"}
          </p>
        </div>
        <Badge tone={categoria.activa ? "success" : "neutral"}>{categoria.activa ? "Activa" : "Inactiva"}</Badge>
      </button>

      {open && total > 0 && (
        <ul className="divide-y divide-line border-t border-line bg-app/60 pl-[52px]">
          {categoria.subcategorias.map((sub) => (
            <li key={sub.id} className="flex items-center justify-between gap-3 py-2.5 pr-4">
              <span className="text-sm text-ink">{sub.nombre}</span>
              <Badge tone={sub.activa ? "success" : "neutral"}>{sub.activa ? "Activa" : "Inactiva"}</Badge>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
