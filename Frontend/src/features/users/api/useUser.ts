import { useQuery } from "@tanstack/react-query";
import { userApi } from "./usersApi";

export function userDetailKey(id: number) {
  return ["users", "detail", id] as const;
}

export function useUser(id: number | undefined) {
  return useQuery({
    queryKey: userDetailKey(id ?? 0),
    queryFn: () => userApi.get(id as number),
    enabled: typeof id === "number" && id > 0,
  });
}
