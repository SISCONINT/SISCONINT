import { useMutation, useQueryClient } from "@tanstack/react-query";
import { authApi } from "./authApi";
import { useAuthStore } from "@/shared/auth/authStore";

export function useLogout() {
    const queryClient = useQueryClient();

    return useMutation({
        mutationFn: authApi.logout,
        onSuccess: ()=>{
            useAuthStore.getState().clear();
            queryClient.cancelQueries();
        }
    });
}