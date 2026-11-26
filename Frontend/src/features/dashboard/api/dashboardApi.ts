import { api } from "@/shared/api/client";
import type { ApiResponse } from "@/shared/api/types";
import type { DashboardFilters, DashboardGerencial, DashboardPersonal } from "../types";

function queryParams(filters: DashboardFilters) {
  return {
    periodo: filters.periodo,
    fecha_desde: filters.periodo === "PERSONALIZADO" ? filters.fecha_desde : undefined,
    fecha_hasta: filters.periodo === "PERSONALIZADO" ? filters.fecha_hasta : undefined,
    cliente: filters.cliente,
    colaborador: filters.colaborador,
  };
}

export const dashboardApi = {
  async getGerencial(filters: DashboardFilters): Promise<DashboardGerencial> {
    const res = await api.get<ApiResponse<DashboardGerencial>>("/dashboard", { params: queryParams(filters) });
    return res.data.data;
  },

  async getPersonal(filters: DashboardFilters): Promise<DashboardPersonal> {
    const res = await api.get<ApiResponse<DashboardPersonal>>("/dashboard/me", { params: queryParams(filters) });
    return res.data.data;
  },
};
