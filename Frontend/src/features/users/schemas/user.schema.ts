import { z } from "zod";
import { ROLES, type Role } from "@/shared/constants/roles";
import { GRADOS } from "../types";

const ROLE_VALUES = Object.values(ROLES) as [Role, ...Role[]];

const phone = z.string().regex(/^[0-9]{10}$/, "Debe tener 10 dígitos");
const optionalMax = (max: number) =>
  z
    .string()
    .max(max, `Máximo ${max} caracteres`)
    .optional()
    .or(z.literal(""));

export const userSchema = z.object({
  nombre_completo: z.string().min(1, "Campo obligatorio").max(150, "Máximo 150 caracteres"),
  telefono_despacho: phone,
  correo_institucional: z.string().min(1, "Campo obligatorio").email("Correo con formato inválido").max(254),
  rol: z.enum(ROLE_VALUES, { message: "Selecciona un rol" }),
  grado_escalafon: z.enum(GRADOS, { message: "Selecciona un grado" }),
  telefono_personal: phone,
  emergencia_nombre: z.string().min(1, "Campo obligatorio").max(150, "Máximo 150 caracteres"),
  emergencia_telefono: phone,
  licenciatura: optionalMax(150),
  cedula: z
    .string()
    .regex(/^[0-9]{7,8}$/, "Debe tener 7 u 8 dígitos")
    .optional()
    .or(z.literal("")),
  calle: optionalMax(150),
  no_ext_int: optionalMax(40),
  colonia: optionalMax(100),
  municipio: optionalMax(100),
  estado: optionalMax(100),
});

export type UserFormValues = z.infer<typeof userSchema>;
