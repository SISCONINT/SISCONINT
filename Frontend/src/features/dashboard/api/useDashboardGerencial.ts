import { useQuery } from "@tanstack/react-query";
import { dashboardApi } from "./dashboardApi";
import type { DashboardFilters } from "../types";

export function useDashboardGerencial(filters: DashboardFilters) {
  return useQuery({
    queryKey: ["dashboard", "gerencial", filters],
    queryFn: () => dashboardApi.getGerencial(filters),
    placeholderData: (prev) => prev,
  });
}
