import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useQueryClient } from "@tanstack/react-query";
import { Plus } from "lucide-react";
import { PageHeader } from "@/shared/components/PageHeader";
import { SearchableSelect } from "@/shared/components/SearchableSelect";
import { inputClass } from "@/shared/components/FormField";
import { ConfirmDialog } from "@/shared/components/ConfirmDialog";
import { ApiError } from "@/shared/api/types";
import { useAuthStore } from "@/shared/auth/authStore";
import { ROLES } from "@/shared/constants/roles";
import { useClienteOptions } from "@/features/clients/api/useClients";
import { useColaboradorOptions } from "@/features/users/api/useUsers";
import { tasksApi } from "../api/tasksApi";
import { useTaskBoard } from "../api/useTasks";
import { KanbanColumn } from "../components/KanbanColumn";
import type { Prioridad } from "../types";

export function KanbanBoardPage() {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const actor = useAuthStore((s) => s.user);
  const canFilterResponsable = actor?.rol !== ROLES.CONTADOR;

  const [clienteId, setClienteId] = useState<number | null>(null);
  const [clienteQuery, setClienteQuery] = useState("");
  const [responsableId, setResponsableId] = useState<number | null>(null);
  const [responsableQuery, setResponsableQuery] = useState("");
  const [prioridad, setPrioridad] = useState<Prioridad | "">("");
  const [conflict, setConflict] = useState<{ taskId: number; estado: string } | null>(null);
  const [dragOverEstado, setDragOverEstado] = useState<string | null>(null);

  const { options: clienteOptions, isLoading: loadingClientes } = useClienteOptions(clienteQuery);
  const { options: responsableOptions, isLoading: loadingResponsables } = useColaboradorOptions(responsableQuery);

  const boardFilters = {
    cliente: clienteId ?? undefined,
    responsable: canFilterResponsable ? responsableId ?? undefined : undefined,
    prioridad: prioridad || undefined,
  };
  const { data, isLoading, isError } = useTaskBoard(boardFilters);

  async function moveTask(taskId: number, estado: string, confirmar: boolean) {
    try {
      await tasksApi.move(taskId, estado, confirmar);
      queryClient.invalidateQueries({ queryKey: ["tasks"] });
      setConflict(null);
    } catch (e) {
      if (e instanceof ApiError && e.status === 409 && e.extra?.subtareas_pendientes) {
        setConflict({ taskId, estado });
      }
    }
  }

  const columnas = data?.columnas ?? [];

  return (
    <div className="flex h-[calc(100vh-56px)] flex-col">
      <PageHeader
        title="Tablero Kanban"
        subtitle="Arrastra una tarjeta entre columnas para cambiar su estado (HU_41–HU_43)."
        actions={
          <button
            type="button"
            onClick={() => navigate("/tareas/nuevo")}
            className="flex items-center gap-2 rounded-lg bg-gold-300 px-4 py-2.5 text-sm font-semibold text-ink hover:brightness-95"
          >
            <Plus size={16} /> Nueva tarea
          </button>
        }
      />

      <div className="mb-4 flex flex-wrap items-center gap-2.5">
        <div className="w-56">
          <SearchableSelect
            value={clienteId}
            onChange={setClienteId}
            options={clienteOptions}
            loading={loadingClientes}
            query={clienteQuery}
            onQueryChange={setClienteQuery}
            placeholder="Filtrar por cliente…"
          />
        </div>
        {canFilterResponsable && (
          <div className="w-56">
            <SearchableSelect
              value={responsableId}
              onChange={setResponsableId}
              options={responsableOptions}
              loading={loadingResponsables}
              query={responsableQuery}
              onQueryChange={setResponsableQuery}
              placeholder="Filtrar por responsable…"
            />
          </div>
        )}
        <select
          value={prioridad}
          onChange={(e) => setPrioridad(e.target.value as Prioridad | "")}
          className={inputClass + " w-44 pl-4"}
        >
          <option value="">Toda prioridad</option>
          <option value="ALTA">Alta</option>
          <option value="MEDIA">Media</option>
          <option value="BAJA">Baja</option>
        </select>
      </div>

      {isLoading ? (
        <p className="text-sm text-muted">Cargando tablero…</p>
      ) : isError ? (
        <p className="text-sm text-danger">No se pudo cargar el tablero.</p>
      ) : data?.mensaje ? (
        <p className="text-sm text-muted">{data.mensaje}</p>
      ) : (
        <div className="flex flex-1 gap-4 overflow-x-auto pb-2">
          {columnas.map((col) => (
            <KanbanColumn
              key={col.estado}
              column={col}
              dragOver={dragOverEstado === col.estado}
              onDragOverChange={(over) => setDragOverEstado(over ? col.estado : null)}
              onDropTask={(taskId, estado) => moveTask(taskId, estado, false)}
            />
          ))}
        </div>
      )}

      <ConfirmDialog
        open={!!conflict}
        title="La tarea tiene subtareas pendientes"
        description="¿Confirmas mover esta tarea a Completado de todas formas? (RG-14)"
        confirmLabel="Mover de todas formas"
        onConfirm={() => conflict && moveTask(conflict.taskId, conflict.estado, true)}
        onCancel={() => setConflict(null)}
      />
    </div>
  );
}
