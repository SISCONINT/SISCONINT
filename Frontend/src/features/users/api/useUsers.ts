import { keepPreviousData, useQuery } from "@tanstack/react-query";
import { userApi } from "./usersApi";
import type { UsersFilters } from "../types";

export function useUsers(filters: UsersFilters) {
  return useQuery({
    queryKey: ["users", filters], // cada combinación de filtros tiene su propia caché
    queryFn: () => userApi.list(filters),
    placeholderData: keepPreviousData, // al cambiar de página no parpadea
  });
}