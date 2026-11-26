import { useAuthStore } from "@/shared/auth/authStore";
import { ROLES } from "@/shared/constants/roles";
import { GerencialDashboard } from "./GerencialDashboard";
import { PersonalDashboard } from "./PersonalDashboard";

export function DashboardPage() {
  const user = useAuthStore((s) => s.user);
  if (user?.rol === ROLES.CONTADOR) return <PersonalDashboard />;
  return <GerencialDashboard />;
}
