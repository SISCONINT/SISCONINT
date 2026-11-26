import { api } from "@/shared/api/client";
import type { ApiResponse } from "@/shared/api/types";
import type { PlantillaCorreo, PlantillaFormValues } from "../types";

export const templatesApi = {
  async list(): Promise<PlantillaCorreo[]> {
    const res = await api.get<ApiResponse<PlantillaCorreo[]>>("/templates");
    return res.data.data;
  },

  async create(values: PlantillaFormValues): Promise<PlantillaCorreo> {
    const res = await api.post<ApiResponse<PlantillaCorreo>>("/templates", values);
    return res.data.data;
  },

  async update(id: number, values: Omit<PlantillaFormValues, "clave">): Promise<PlantillaCorreo> {
    const res = await api.put<ApiResponse<PlantillaCorreo>>(`/templates/${id}`, values);
    return res.data.data;
  },
};
