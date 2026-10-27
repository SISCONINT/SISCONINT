import { useMutation, useQueryClient } from "@tanstack/react-query";
import { userApi } from "./usersApi";

export function useCreateUser(){
    const queryClient = useQueryClient();

    return useMutation({
        mutationFn: userApi.create,
        onSuccess: () => {
            queryClient.invalidateQueries({queryKey: ["users"]});
        }
    });
}