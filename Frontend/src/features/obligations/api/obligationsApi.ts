import { api } from "@/shared/api/client";
import type { ApiResponse } from "@/shared/api/types";
import type { Obligacion, ObligacionFilters } from "../types";

interface Payload {
  cliente_id: number;
  categoria_id?: number;
  nombre: string;
  periodicidad: string;
  dia_limite: number;
  notas?: string;
}

export const obligationsApi = {
  async list(filters: ObligacionFilters) {
    const res = await api.get<ApiResponse<Obligacion[]>>("/obligations", {
      params: { cliente: filters.cliente, solo_activas: filters.solo_activas, page: filters.page },
    });
    return { items: res.data.data, meta: res.data.meta! };
  },

  async create(payload: Payload): Promise<Obligacion> {
    const res = await api.post<ApiResponse<Obligacion>>("/obligations", payload);
    return res.data.data;
  },

  async update(id: number, payload: Payload & { activa: boolean }): Promise<Obligacion> {
    const res = await api.put<ApiResponse<Obligacion>>(`/obligations/${id}`, payload);
    return res.data.data;
  },

  async deactivate(id: number): Promise<Obligacion> {
    const res = await api.post<ApiResponse<Obligacion>>(`/obligations/${id}/deactivate`);
    return res.data.data;
  },
};
