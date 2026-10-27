import { useAuthStore } from "@/shared/auth/authStore";
import { ROLES } from "@/shared/constants/roles";
import { GerencialDashboard } from "./GerencialDashboard";
import { ContadorDashboard } from "./ContadorDashboard";

export function DashboardPage() {
  const user = useAuthStore((s) => s.user);
  if (user?.rol === ROLES.CONTADOR) return <ContadorDashboard />;
  return <GerencialDashboard />;
}
