import { keepPreviousData, useQuery } from "@tanstack/react-query";
import { ROLES } from "@/shared/constants/roles";
import { userApi } from "./usersApi";

const FILTERS = { search: "", rol: ROLES.DUENO, estatus: "ACTIVO" as const, page: 1 };

export function useActiveDuenoCount(enabled: boolean) {
  return useQuery({
    queryKey: ["users", FILTERS],
    queryFn: () => userApi.list(FILTERS),
    select: (page) => page.meta.total,
    placeholderData: keepPreviousData,
    enabled,
  });
}
