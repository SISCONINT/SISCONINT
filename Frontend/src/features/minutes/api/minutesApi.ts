import { api } from "@/shared/api/client";
import type { ApiResponse } from "@/shared/api/types";
import type { Minuta, MinutaFilters } from "../types";

interface Payload {
  cliente_id?: number;
  tarea_id?: number;
  titulo: string;
  fecha: string;
  participantes?: string;
  acuerdos: string;
}

export const minutesApi = {
  async list(filters: MinutaFilters) {
    const res = await api.get<ApiResponse<Minuta[]>>("/minutes", { params: { cliente: filters.cliente, page: filters.page } });
    return { items: res.data.data, meta: res.data.meta! };
  },

  async create(payload: Payload): Promise<Minuta> {
    const res = await api.post<ApiResponse<Minuta>>("/minutes", payload);
    return res.data.data;
  },

  async remove(id: number): Promise<void> {
    await api.delete(`/minutes/${id}`);
  },
};
