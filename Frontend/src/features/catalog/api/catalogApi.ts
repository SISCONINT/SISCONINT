import { api } from "@/shared/api/client";
import type { ApiResponse } from "@/shared/api/types";
import { toQueryParams } from "@/shared/utils/format";
import type { CatalogFilters, Categoria } from "../types";

export const catalogApi = {
  list: async (filters: CatalogFilters) => {
    const res = await api.get<ApiResponse<Categoria[]>>("/catalog", {
      params: toQueryParams(filters),
    });
    return res.data.data;
  },
};
