import { Navigate } from "react-router-dom";
import type { ReactNode } from "react";
import type { Role } from "../../shared/constants/roles";
import { useAuthStore } from "./authStore";

export function RequireRole({ roles, children }: { roles: Role[]; children: ReactNode }) {
  const user = useAuthStore((s) => s.user);
  if (!user || !roles.includes(user.rol)) return <Navigate to="/dashboard" replace />;
  return <>{children}</>;
}