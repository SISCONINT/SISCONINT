import { api } from "@/shared/api/client";
import type { ApiResponse } from "@/shared/api/types";
import { toQueryParams } from "@/shared/utils/format";
import type {
  TareaBoard,
  TareaBoardFilters,
  TareaDetalle,
  TareaFormValues,
  TareaListFilters,
  TareaListItem,
} from "../types";

function toPayload(v: TareaFormValues) {
  return {
    titulo: v.titulo,
    descripcion: v.descripcion || null,
    cliente_id: v.cliente_id,
    categoria_id: v.categoria_id,
    asignado_id: v.asignado_id,
    fecha_limite: v.fecha_limite,
    hora_limite: v.hora_limite || undefined,
    prioridad: v.prioridad,
    horas_estimadas: v.horas_estimadas ? Number(v.horas_estimadas) : null,
    notificar_cliente: v.notificar_cliente,
  };
}

export const tasksApi = {
  list: async (filters: TareaListFilters) => {
    const res = await api.get<ApiResponse<TareaListItem[]>>("/tasks", { params: toQueryParams(filters) });
    return res.data;
  },

  board: async (filters: TareaBoardFilters) => {
    const res = await api.get<ApiResponse<TareaBoard>>("/tasks/board", { params: toQueryParams(filters) });
    return res.data.data;
  },

  get: async (id: number) => {
    const res = await api.get<ApiResponse<TareaDetalle>>(`/tasks/${id}`);
    return res.data.data;
  },

  create: async (values: TareaFormValues) => {
    const res = await api.post<ApiResponse<{ id: number }>>("/tasks", toPayload(values));
    return res.data.data;
  },

  update: async (id: number, values: TareaFormValues) => {
    const res = await api.put<ApiResponse<TareaDetalle>>(`/tasks/${id}`, toPayload(values));
    return res.data.data;
  },

  move: async (id: number, estado: string, confirmarSubtareasPendientes = false) => {
    const res = await api.patch<ApiResponse<TareaDetalle>>(`/tasks/${id}/estado`, {
      estado,
      confirmar_subtareas_pendientes: confirmarSubtareasPendientes,
    });
    return res.data.data;
  },

  remove: async (id: number) => {
    await api.delete(`/tasks/${id}`);
  },
};
