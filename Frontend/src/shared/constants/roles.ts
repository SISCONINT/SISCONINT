export const ROLES = {
  DUENO: "DUENO",
  ADMINISTRADOR: "ADMINISTRADOR",
  COORDINADOR: "COORDINADOR",
  CONTADOR: "CONTADOR",
} as const;

export type Role = (typeof ROLES)[keyof typeof ROLES];

export const ROLE_LABELS: Record<Role, string> = {
  DUENO: "Socio Director",
  ADMINISTRADOR: "Administrador",
  COORDINADOR: "Coordinador",
  CONTADOR: "Contador",
};