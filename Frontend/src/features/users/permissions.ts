import { ROLES, type Role } from "@/shared/constants/roles";

const { DUENO, ADMINISTRADOR, COORDINADOR, CONTADOR } = ROLES;

/** Espejo de ASSIGNABLE_ROLES del backend (app/core/permissions.py): qué roles puede asignar cada actor. */
const ASSIGNABLE_ROLES: Record<string, Role[]> = {
  [DUENO]: [DUENO, ADMINISTRADOR, COORDINADOR, CONTADOR],
  [ADMINISTRADOR]: [COORDINADOR, CONTADOR],
};

export function assignableRoles(actorRol: Role): Role[] {
  return ASSIGNABLE_ROLES[actorRol] ?? [];
}

/** Espejo de ROLES_PROTECTED_FROM_ADMIN: el Administrador no edita Dueño ni Administrador. */
export function canActorEditTarget(actorRol: Role, targetRol: Role): boolean {
  if (actorRol === DUENO) return true;
  if (actorRol === ADMINISTRADOR) return targetRol !== DUENO && targetRol !== ADMINISTRADOR;
  return false;
}
