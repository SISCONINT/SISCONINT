import { api } from "@/shared/api/client";
import type { ApiResponse } from "@/shared/api/types";
import { toQueryParams } from "@/shared/utils/format";
import type {
  Colaborador,
  ColaboradorFilters,
  ColaboradorFormValues,
  ColaboradorListItem,
  DeactivationImpact,
} from "../types";

export const usersApi = {
  list: async (filters: ColaboradorFilters) => {
    const res = await api.get<ApiResponse<ColaboradorListItem[]>>("/users", {
      params: toQueryParams(filters),
    });
    return res.data;
  },

  get: async (id: number) => {
    const res = await api.get<ApiResponse<Colaborador>>(`/users/${id}`);
    return res.data.data;
  },

  create: async (data: ColaboradorFormValues) => {
    const res = await api.post<ApiResponse<Colaborador & { correo_activacion_enviado: boolean }>>("/users", data);
    return res.data.data;
  },

  update: async (id: number, data: ColaboradorFormValues) => {
    const res = await api.put<ApiResponse<Colaborador>>(`/users/${id}`, data);
    return res.data.data;
  },

  deactivationImpact: async (id: number) => {
    const res = await api.get<ApiResponse<DeactivationImpact>>(`/users/${id}/deactivation-impact`);
    return res.data.data;
  },

  deactivate: async (id: number, reasignarA?: number | null) => {
    const res = await api.post<ApiResponse<Colaborador>>(`/users/${id}/deactivate`, {
      reasignar_a: reasignarA ?? null,
    });
    return res.data.data;
  },
};
