import {PHONE_REGEX, CEDULA_REGEX} from "@/shared/utils/validators"
import { GRADOS } from "@/shared/constants/grados";
import { ROLES } from "@/shared/constants/roles";
import { z } from "zod";

const required = (max: number)=>
    z.string().trim().min(1, "Campo obligatorio").max(max, `Máximo ${max} caracteres`);

const optional = (max: number) =>
    z.string().trim().max(max, `Máximo ${max} caracteres`)

const phone = z.string().trim().min(1, "Campo obligatorio").regex(PHONE_REGEX, "Debe tener 10 dígitos");

export const userSchema = z.object({
    // Campos obligatorios para crear a un colaborador
    nombre_completo: required(150),
    correo_institucional: required(254).email("Correo con formato inválido"),
    
    rol:z.enum(ROLES, {error: "Campo obligatorio"}),
    grado_escalafon: z.enum(GRADOS, {error: "Campo obligatorio"}),
    
    telefono_despacho: phone,
    telefono_personal: phone,
    emergencia_nombre: required(150),
    emergencia_telefono: phone,

    // Campos opcionales
    licenciatura: optional(150),
    cedula: z.string().trim().regex(CEDULA_REGEX, "Debe tener 7 u 8 dígitos").or(z.literal("")),

    calle: optional(150),
    no_ext_int: optional(40),
    colonia: optional(100),
    municipio: optional(100),
    estado: optional(100),

    //la expresion .or(z.literal("")) funciona para poder enviar campos vacios
});

export type RegisterUserFormValues = z.infer<typeof userSchema>;