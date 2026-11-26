import { api } from "@/shared/api/client";
import type { ApiResponse } from "@/shared/api/types";
import type { TarifaRow } from "../types";

export const ratesApi = {
  async list(): Promise<TarifaRow[]> {
    const res = await api.get<ApiResponse<TarifaRow[]>>("/rates");
    return res.data.data;
  },

  async upsert(colaboradorId: number, montoHora: number): Promise<void> {
    await api.put(`/rates/${colaboradorId}`, { monto_hora: montoHora, moneda: "MXN" });
  },
};
