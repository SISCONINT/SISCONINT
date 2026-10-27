import { useMutation } from "@tanstack/react-query";
import { authApi } from "./authApi";

export function useActivateAccount() {
  // Sin onSuccess aquí: qué mostrar al terminar lo decide la pantalla
  return useMutation({ mutationFn: authApi.activate });
}