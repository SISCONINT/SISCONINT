import { Link } from "react-router-dom";
import { Clock } from "lucide-react";
import { Avatar } from "@/shared/components/Avatar";
import { PrioridadBadge, SemaforoDot } from "@/shared/components/Badge";
import { formatDate } from "@/shared/utils/format";
import type { TareaBoardCard } from "../types";

interface Props {
  tarea: TareaBoardCard;
  draggable?: boolean;
  onDragStart?: (e: React.DragEvent) => void;
}

export function TaskCard({ tarea, draggable, onDragStart }: Props) {
  return (
    <Link
      to={`/tareas/${tarea.id}`}
      draggable={draggable}
      onDragStart={onDragStart}
      className="block cursor-grab rounded-xl border border-line bg-surface p-3.5 shadow-card transition hover:border-gold-500 active:cursor-grabbing"
    >
      <div className="mb-2 flex items-start justify-between gap-2">
        <SemaforoDot semaforo={tarea.semaforo} />
        <PrioridadBadge prioridad={tarea.prioridad} />
      </div>
      <p className="mb-1.5 line-clamp-2 text-sm font-semibold text-ink">{tarea.titulo}</p>
      <p className="mb-3 truncate text-[12px] text-muted">{tarea.cliente_nombre ?? "Sin cliente"}</p>
      <div className="flex items-center justify-between">
        <span className="flex items-center gap-1 text-[11px] text-muted">
          <Clock size={12} /> {formatDate(tarea.fecha_limite)}
        </span>
        <Avatar nombre={tarea.asignado_nombre} size={24} />
      </div>
    </Link>
  );
}
