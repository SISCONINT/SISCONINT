import { Navigate, Outlet } from "react-router-dom";
import { useAuthStore } from "./authStore";

export function RequireAuth() {
  const status = useAuthStore((s) => s.status);
  if (status === "checking") {
    return <div className="grid min-h-screen place-items-center text-muted">Cargando…</div>;
  }
  if (status === "anonymous") return <Navigate to="/login" replace />;
  return <Outlet />;
}

/** Evita que un usuario con sesión vea /login */
export function GuestOnly() {
  const status = useAuthStore((s) => s.status);
  if (status === "checking") return null;
  if (status === "authenticated") return <Navigate to="/dashboard" replace />;
  return <Outlet />;
}