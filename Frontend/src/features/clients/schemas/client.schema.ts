import { z } from "zod";

const phone = z.string().regex(/^[0-9]{10}$/, "Debe tener 10 dígitos");
const RFC_MORAL = /^[A-ZÑ&]{3}[0-9]{6}[A-Z0-9]{3}$/;
const RFC_FISICA = /^[A-ZÑ&]{4}[0-9]{6}[A-Z0-9]{3}$/;

const contactoSchema = z.object({
  nombre_completo: z.string().min(1, "Campo obligatorio").max(150),
  telefono: phone,
  correo: z.string().min(1, "Campo obligatorio").email("Correo con formato inválido"),
  cargo: z.string().min(1, "Campo obligatorio").max(100),
});

const contactoVacio = { nombre_completo: "", telefono: "", correo: "", cargo: "" };

export const clientSchema = z
  .object({
    nombre_completo: z.string().min(1, "Campo obligatorio").max(200, "Máximo 200 caracteres"),
    rfc: z.string().min(1, "Campo obligatorio").transform((v) => v.toUpperCase()),
    tipo_persona: z.enum(["FISICA", "MORAL"], { message: "Selecciona el tipo de persona" }),
    razon_social: z.string().max(250).optional().or(z.literal("")),
    forma_pago: z.enum(["EFECTIVO", "TRANSFERENCIA"], { message: "Selecciona una forma de pago" }),
    contador_asignado_id: z.number({ message: "Selecciona un contador" }).nullable().refine((v) => v !== null, "Selecciona un contador"),
    giro: z.string().min(1, "Campo obligatorio").max(150),
    telefono: phone,
    correo: z.string().min(1, "Campo obligatorio").email("Correo con formato inválido"),
    codigo_postal: z.string().regex(/^[0-9]{5}$/, "Debe tener 5 dígitos"),
    calle: z.string().min(1, "Campo obligatorio").max(150),
    no_exterior: z.string().min(1, "Campo obligatorio").max(20),
    no_interior: z.string().max(20).optional().or(z.literal("")),
    colonia: z.string().min(1, "Campo obligatorio").max(100),
    ciudad: z.string().min(1, "Campo obligatorio").max(100),
    estado: z.string().min(1, "Campo obligatorio").max(100),
    regimenes: z.array(z.string()).min(1, "Selecciona al menos un régimen"),
    tiene_trabajadores: z.boolean(),
    tipo_nomina: z.enum(["SEMANAL", "QUINCENAL", "MENSUAL", ""]).optional(),
    contacto_principal: contactoSchema,
    tiene_contacto_pagos: z.boolean(),
    contacto_pagos: contactoSchema.partial().optional(),
  })
  .superRefine((data, ctx) => {
    if (data.tipo_persona === "MORAL") {
      if (!data.razon_social) {
        ctx.addIssue({ code: "custom", path: ["razon_social"], message: "Campo obligatorio" });
      }
      if (data.rfc.length !== 12) {
        ctx.addIssue({ code: "custom", path: ["rfc"], message: "El RFC de persona Moral debe tener 12 caracteres" });
      } else if (!RFC_MORAL.test(data.rfc)) {
        ctx.addIssue({ code: "custom", path: ["rfc"], message: "El RFC no tiene un formato válido" });
      }
    } else {
      if (data.rfc.length !== 13) {
        ctx.addIssue({ code: "custom", path: ["rfc"], message: "El RFC de persona Física debe tener 13 caracteres" });
      } else if (!RFC_FISICA.test(data.rfc)) {
        ctx.addIssue({ code: "custom", path: ["rfc"], message: "El RFC no tiene un formato válido" });
      }
    }

    if (data.tiene_trabajadores && !data.tipo_nomina) {
      ctx.addIssue({ code: "custom", path: ["tipo_nomina"], message: "Campo obligatorio" });
    }

    if (data.tiene_contacto_pagos) {
      const p = data.contacto_pagos;
      if (!p?.nombre_completo) ctx.addIssue({ code: "custom", path: ["contacto_pagos", "nombre_completo"], message: "Campo obligatorio" });
      if (!p?.telefono || !/^[0-9]{10}$/.test(p.telefono)) ctx.addIssue({ code: "custom", path: ["contacto_pagos", "telefono"], message: "Debe tener 10 dígitos" });
      if (!p?.correo) ctx.addIssue({ code: "custom", path: ["contacto_pagos", "correo"], message: "Campo obligatorio" });
      if (!p?.cargo) ctx.addIssue({ code: "custom", path: ["contacto_pagos", "cargo"], message: "Campo obligatorio" });
    }
  });

export type ClientSchemaValues = z.infer<typeof clientSchema>;
export const emptyContacto = contactoVacio;
