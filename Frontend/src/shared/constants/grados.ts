export const GRADOS = {
    JUNIOR: "JUNIOR",
    SENIOR: "SENIOR",
    ADMIN: "ADMIN",
} as const;

export type Grado = (typeof GRADOS)[keyof typeof GRADOS];

export const GRADO_LABELS: Record<Grado, string> ={
    JUNIOR: "Junior",
    SENIOR: "Senior",
    ADMIN: "Admin",
};