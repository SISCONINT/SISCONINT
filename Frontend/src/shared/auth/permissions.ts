import {
  LayoutDashboard, Columns3, CheckSquare, CalendarDays,
  Users, Repeat, FileText, Timer,
  AlertTriangle, Bell, BarChart3,
  UserCog, Banknote, ListTree, Mail,
  type LucideIcon,
} from "lucide-react";
import { ROLES, type Role } from "../../shared/constants/roles";

const { DUENO, ADMINISTRADOR, COORDINADOR, CONTADOR } = ROLES;
const ALL: Role[] = [DUENO, ADMINISTRADOR, COORDINADOR, CONTADOR];
const GERENCIA: Role[] = [DUENO, ADMINISTRADOR, COORDINADOR];
const ADMIN: Role[] = [DUENO, ADMINISTRADOR];

export interface NavItem { label: string; path: string; icon: LucideIcon; roles: Role[]; }
export interface NavSection { title: string; items: NavItem[]; }

export const NAV_SECTIONS: NavSection[] = [
  {
    title: "PRINCIPAL",
    items: [
      { label: "Dashboard", path: "/dashboard", icon: LayoutDashboard, roles: ALL },
      { label: "Tablero Kanban", path: "/tablero", icon: Columns3, roles: ALL },
      { label: "Tareas", path: "/tareas", icon: CheckSquare, roles: ALL },
      { label: "Calendario", path: "/calendario", icon: CalendarDays, roles: ALL },
    ],
  },
  {
    title: "GESTIÓN",
    items: [
      { label: "Clientes", path: "/clientes", icon: Users, roles: ALL },
      { label: "Obligaciones periódicas", path: "/obligaciones", icon: Repeat, roles: ALL },
      { label: "Minutas", path: "/minutas", icon: FileText, roles: ALL },
      { label: "Registro de tiempos", path: "/tiempos", icon: Timer, roles: ALL },
    ],
  },
  {
    title: "CONTROL Y ANÁLISIS",
    items: [
      { label: "Alertas fiscales", path: "/alertas", icon: AlertTriangle, roles: GERENCIA },
      { label: "Notificaciones", path: "/notificaciones", icon: Bell, roles: ALL },
      { label: "Reportes ejecutivos", path: "/reportes", icon: BarChart3, roles: GERENCIA },
    ],
  },
  {
    title: "ADMINISTRACIÓN",
    items: [
      { label: "Colaboradores", path: "/colaboradores", icon: UserCog, roles: ADMIN },
      { label: "Tarifas", path: "/tarifas", icon: Banknote, roles: ADMIN },
      { label: "Catálogo de servicios", path: "/catalogo", icon: ListTree, roles: ALL },
      { label: "Plantillas de correo", path: "/plantillas", icon: Mail, roles: ADMIN },
    ],
  },
];

export function getNavForRole(role: Role): NavSection[] {
  return NAV_SECTIONS
    .map((s) => ({ ...s, items: s.items.filter((i) => i.roles.includes(role)) }))
    .filter((s) => s.items.length > 0);
}

export const ASSIGNABLE_ROLES: Record<Role,Role[]> = {
  [DUENO] : [DUENO, ADMINISTRADOR, COORDINADOR, CONTADOR],
  [ADMINISTRADOR]: [COORDINADOR, CONTADOR],
  [COORDINADOR]: [],
  [CONTADOR]: [],
};

/** El Administrador no edita a Dueño ni a otro Administrador (HU_08). */
const ROLES_PROTECTED_FROM_ADMIN: Role[] = [DUENO, ADMINISTRADOR];

export function canEditCollaborator(actorRol: Role, targetRol: Role): boolean {
  if (actorRol === DUENO) return true;
  if (actorRol === ADMINISTRADOR) return !ROLES_PROTECTED_FROM_ADMIN.includes(targetRol);
  return false;
}