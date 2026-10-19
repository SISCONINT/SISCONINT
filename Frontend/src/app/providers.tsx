import { useEffect, type ReactNode } from "react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { authApi } from "../features/auth/api/authApi";
import { useAuthStore } from "../shared/auth/authStore";

const queryClient = new QueryClient({
  defaultOptions: { queries: { retry: 1, refetchOnWindowFocus: false } },
});

/** Al cargar la app pregunta al backend si ya hay sesión (cookie vigente). */
function AuthBootstrap({ children }: { children: ReactNode }) {
  const { setUser, clear } = useAuthStore.getState();

  useEffect(() => {
    authApi.me().then(setUser).catch(clear);
  }, [setUser, clear]);

  return <>{children}</>;
}

export function Providers({ children }: { children: ReactNode }) {
  return (
    <QueryClientProvider client={queryClient}>
      <AuthBootstrap>{children}</AuthBootstrap>
    </QueryClientProvider>
  );
}