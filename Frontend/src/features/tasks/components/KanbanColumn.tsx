import clsx from "clsx";
import type { TareaBoardColumn } from "../types";
import { TaskCard } from "./TaskCard";

interface Props {
  column: TareaBoardColumn;
  onDropTask: (taskId: number, estado: string) => void;
  dragOver: boolean;
  onDragOverChange: (over: boolean) => void;
}

const COLUMN_ACCENT: Record<string, string> = {
  POR_HACER: "bg-muted",
  EN_PROGRESO: "bg-navy-700",
  EN_REVISION: "bg-amber-500",
  COMPLETADO: "bg-emerald-500",
};

export function KanbanColumn({ column, onDropTask, dragOver, onDragOverChange }: Props) {
  return (
    <div
      onDragOver={(e) => {
        e.preventDefault();
        onDragOverChange(true);
      }}
      onDragLeave={() => onDragOverChange(false)}
      onDrop={(e) => {
        e.preventDefault();
        onDragOverChange(false);
        const taskId = Number(e.dataTransfer.getData("text/task-id"));
        if (taskId) onDropTask(taskId, column.estado);
      }}
      className={clsx(
        "flex w-[280px] shrink-0 flex-col rounded-2xl bg-app/70 p-3 transition",
        dragOver && "ring-2 ring-gold-500",
      )}
    >
      <div className="mb-3 flex items-center gap-2 px-1">
        <span className={clsx("size-2.5 rounded-full", COLUMN_ACCENT[column.estado] ?? "bg-muted")} />
        <h3 className="text-sm font-semibold text-ink">{column.titulo}</h3>
        <span className="ml-auto rounded-full bg-field px-2 py-0.5 text-[11px] font-semibold text-muted">
          {column.total}
        </span>
      </div>
      <div className="flex flex-1 flex-col gap-2.5 overflow-y-auto">
        {column.tareas.map((t) => (
          <TaskCard
            key={t.id}
            tarea={t}
            draggable
            onDragStart={(e) => e.dataTransfer.setData("text/task-id", String(t.id))}
          />
        ))}
        {column.tareas.length === 0 && (
          <p className="rounded-lg border border-dashed border-line p-4 text-center text-[12px] text-muted">
            Sin tareas
          </p>
        )}
      </div>
    </div>
  );
}
