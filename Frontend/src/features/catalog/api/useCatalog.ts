import { useQuery } from "@tanstack/react-query";
import { catalogApi } from "./catalogApi";
import type { CatalogFilters } from "../types";

export function useCatalog(filters: CatalogFilters) {
  return useQuery({
    queryKey: ["catalog", filters],
    queryFn: () => catalogApi.list(filters),
    placeholderData: (prev) => prev,
  });
}
