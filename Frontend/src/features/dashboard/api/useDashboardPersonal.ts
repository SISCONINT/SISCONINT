import { useQuery } from "@tanstack/react-query";
import { dashboardApi } from "./dashboardApi";
import type { DashboardFilters } from "../types";

export function useDashboardPersonal(filters: DashboardFilters) {
  return useQuery({
    queryKey: ["dashboard", "personal", filters],
    queryFn: () => dashboardApi.getPersonal(filters),
    placeholderData: (prev) => prev,
  });
}
