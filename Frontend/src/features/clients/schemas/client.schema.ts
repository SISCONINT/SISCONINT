import { z } from "zod";
import { PHONE_REGEX } from "@/shared/utils/validators";
import type { ClienteCreatePayload, ContactoCliente } from "../types";

const RFC_PATTERN = /^(?:[A-ZÑ&]{4}[0-9]{6}[A-Z0-9]{3}|[A-ZÑ&]{3}[0-9]{6}[A-Z0-9]{3})$/i;
const RFC_FISICA = /^[A-ZÑ&]{4}[0-9]{6}[A-Z0-9]{3}$/i;
const RFC_MORAL = /^[A-ZÑ&]{3}[0-9]{6}[A-Z0-9]{3}$/i;

const requiredText = (max: number) =>
  z.string().trim().min(1, "Campo obligatorio").max(max, `Máximo ${max} caracteres`);

const optionalText = (max: number) =>
  z.string().trim().max(max, `Máximo ${max} caracteres`);

const phone = z
  .string()
  .trim()
  .min(1, "Campo obligatorio")
  .regex(PHONE_REGEX, "Debe tener 10 dígitos");

const optionalPhone = z
  .string()
  .trim()
  .refine((value) => value === "" || PHONE_REGEX.test(value), "Debe tener 10 dígitos");

const email = z
  .string()
  .trim()
  .min(1, "Campo obligatorio")
  .max(254, "Máximo 254 caracteres")
  .email("Correo con formato inválido");

const optionalEmail = z
  .string()
  .trim()
  .refine(
    (value) => value === "" || z.string().email().safeParse(value).success,
    "Correo con formato inválido",
  );

const contactoPrincipalSchema = z.object({
  nombre_completo: requiredText(150),
  telefono: phone,
  correo: email,
  cargo: requiredText(100),
});

const contactoPagosSchema = z.object({
  nombre_completo: optionalText(150),
  telefono: optionalPhone,
  correo: optionalEmail,
  cargo: optionalText(100),
});

const baseClientSchema = z.object({
  tipo_persona: z.enum(["FISICA", "MORAL"], { error: "Selecciona el tipo de persona" }),
  rfc: z
    .string()
    .trim()
    .min(12, "El RFC debe tener 12 o 13 caracteres")
    .max(13, "El RFC debe tener 12 o 13 caracteres")
    .regex(RFC_PATTERN, "El RFC no tiene un formato válido"),
  nombre_completo: requiredText(200),
  razon_social: optionalText(250),
  giro: requiredText(150),
  forma_pago: z.enum(["EFECTIVO", "TRANSFERENCIA"], { error: "Selecciona la forma de pago" }),
  contador_asignado_id: z.string().min(1, "Selecciona al contador responsable"),
  telefono: phone,
  correo: email,

  codigo_postal: z
    .string()
    .trim()
    .regex(/^\d{5}$/, "El código postal debe tener 5 dígitos"),
  calle: requiredText(150),
  no_exterior: requiredText(20),
  no_interior: optionalText(20),
  colonia: requiredText(100),
  ciudad: requiredText(100),
  estado: requiredText(100),

  regimenes: z.array(z.string()).min(1, "Selecciona al menos un régimen fiscal"),

  tiene_trabajadores: z.boolean(),
  tipo_nomina: z.enum(["SEMANAL", "QUINCENAL", "MENSUAL"]).or(z.literal("")),

  contacto_principal: contactoPrincipalSchema,
  contacto_pagos: contactoPagosSchema,
});

export const clientSchema = baseClientSchema.superRefine((data, ctx) => {
  if (data.tipo_persona === "MORAL") {
    if (!data.razon_social) {
      ctx.addIssue({ code: "custom", path: ["razon_social"], message: "Campo obligatorio" });
    }
    if (!RFC_MORAL.test(data.rfc)) {
      ctx.addIssue({
        code: "custom",
        path: ["rfc"],
        message: "El RFC de persona moral debe tener 12 caracteres",
      });
    }
  } else if (!RFC_FISICA.test(data.rfc)) {
    ctx.addIssue({
      code: "custom",
      path: ["rfc"],
      message: "El RFC de persona física debe tener 13 caracteres",
    });
  }

  if (data.tiene_trabajadores && !data.tipo_nomina) {
    ctx.addIssue({
      code: "custom",
      path: ["tipo_nomina"],
      message: "Selecciona la periodicidad de la nómina",
    });
  }
  if (!data.tiene_trabajadores && data.tipo_nomina) {
    ctx.addIssue({
      code: "custom",
      path: ["tipo_nomina"],
      message: "No aplica cuando el contribuyente no tiene trabajadores",
    });
  }

  // Regla "todo o nada" del contacto de pagos (misma validación que el backend).
  const pagos = data.contacto_pagos;
  const valores = [pagos.nombre_completo, pagos.telefono, pagos.correo, pagos.cargo];
  const capturados = valores.filter((value) => value !== "").length;
  if (capturados > 0 && capturados < valores.length) {
    const campos: { key: keyof typeof pagos; message: string }[] = [
      { key: "nombre_completo", message: "Completa el nombre o deja vacío todo el contacto" },
      { key: "telefono", message: "Completa el teléfono o deja vacío todo el contacto" },
      { key: "correo", message: "Completa el correo o deja vacío todo el contacto" },
      { key: "cargo", message: "Completa el cargo o deja vacío todo el contacto" },
    ];
    campos.forEach(({ key, message }) => {
      if (!pagos[key]) {
        ctx.addIssue({ code: "custom", path: ["contacto_pagos", key], message });
      }
    });
  }
});

export type ClientFormValues = z.infer<typeof clientSchema>;

export const EMPTY_CLIENT_FORM: ClientFormValues = {
  tipo_persona: "MORAL",
  rfc: "",
  nombre_completo: "",
  razon_social: "",
  giro: "",
  forma_pago: "TRANSFERENCIA",
  contador_asignado_id: "",
  telefono: "",
  correo: "",
  codigo_postal: "",
  calle: "",
  no_exterior: "",
  no_interior: "",
  colonia: "",
  ciudad: "",
  estado: "",
  regimenes: [],
  tiene_trabajadores: false,
  tipo_nomina: "",
  contacto_principal: {
    nombre_completo: "",
    telefono: "",
    correo: "",
    cargo: "",
  },
  contacto_pagos: {
    nombre_completo: "",
    telefono: "",
    correo: "",
    cargo: "",
  },
};

/** Rutas válidas para pintar errores de servidor junto a cada campo. */
export const CLIENT_FIELD_PATHS = new Set<string>([
  ...Object.keys(baseClientSchema.shape),
  "contacto_principal.nombre_completo",
  "contacto_principal.telefono",
  "contacto_principal.correo",
  "contacto_principal.cargo",
  "contacto_pagos.nombre_completo",
  "contacto_pagos.telefono",
  "contacto_pagos.correo",
  "contacto_pagos.cargo",
]);

const cleanContact = (contacto: ContactoCliente): ContactoCliente => ({
  nombre_completo: contacto.nombre_completo.trim(),
  telefono: contacto.telefono.trim(),
  correo: contacto.correo.trim(),
  cargo: contacto.cargo.trim(),
});

export function toCreatePayload(values: ClientFormValues): ClienteCreatePayload {
  const pagos = values.contacto_pagos;
  const tienePagos = Object.values(pagos).some((value) => value.trim() !== "");

  return {
    nombre_completo: values.nombre_completo.trim(),
    rfc: values.rfc.trim().toUpperCase(),
    tipo_persona: values.tipo_persona,
    razon_social:
      values.tipo_persona === "MORAL" ? values.razon_social.trim() : undefined,
    forma_pago: values.forma_pago,
    contador_asignado_id: Number(values.contador_asignado_id),
    giro: values.giro.trim(),
    telefono: values.telefono.trim(),
    correo: values.correo.trim(),
    codigo_postal: values.codigo_postal.trim(),
    calle: values.calle.trim(),
    no_exterior: values.no_exterior.trim(),
    no_interior: values.no_interior.trim() || undefined,
    colonia: values.colonia.trim(),
    ciudad: values.ciudad.trim(),
    estado: values.estado.trim(),
    regimenes: values.regimenes,
    tiene_trabajadores: values.tiene_trabajadores,
    tipo_nomina: values.tiene_trabajadores && values.tipo_nomina ? values.tipo_nomina : undefined,
    contacto_principal: cleanContact(values.contacto_principal),
    contacto_pagos: tienePagos ? cleanContact(pagos) : undefined,
  };
}
