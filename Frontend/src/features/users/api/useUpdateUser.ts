import { useMutation, useQueryClient } from "@tanstack/react-query";
import type { RegisterUserFormValues } from "../schemas/user.schema";
import { userApi } from "./usersApi";
import { userDetailKey } from "./useUser";

export function useUpdateUser(id: number) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (values: RegisterUserFormValues) => userApi.update(id, values),
    onSuccess: (colaborador) => {
      queryClient.setQueryData(userDetailKey(id), colaborador);
      queryClient.invalidateQueries({ queryKey: ["users"] });
    },
  });
}
