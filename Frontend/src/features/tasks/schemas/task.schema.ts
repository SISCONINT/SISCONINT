import { z } from "zod";

function todayMx(): string {
  return new Date().toLocaleDateString("en-CA", { timeZone: "America/Mexico_City" });
}

export const taskSchema = z.object({
  titulo: z.string().min(5, "Mínimo 5 caracteres").max(100, "Máximo 100 caracteres"),
  descripcion: z.string().max(2000, "Máximo 2000 caracteres").optional().or(z.literal("")),
  cliente_id: z.number({ message: "Selecciona un cliente" }).nullable().refine((v) => v !== null, "Selecciona un cliente"),
  categoria_id: z.number({ message: "Selecciona una categoría" }).nullable().refine((v) => v !== null, "Selecciona una categoría"),
  asignado_id: z.number({ message: "Selecciona un responsable" }).nullable().refine((v) => v !== null, "Selecciona un responsable"),
  fecha_limite: z
    .string()
    .min(1, "Campo obligatorio")
    .refine((v) => v >= todayMx(), "La fecha límite debe ser hoy o posterior"),
  hora_limite: z.string().min(1, "Campo obligatorio"),
  prioridad: z.enum(["BAJA", "MEDIA", "ALTA"], { message: "Selecciona una prioridad" }),
  horas_estimadas: z
    .string()
    .optional()
    .or(z.literal(""))
    .refine((v) => !v || (Number(v) >= 0.5 && Number(v) <= 200 && (Number(v) * 2) % 1 === 0), {
      message: "Debe ser entre 0.5 y 200, en múltiplos de 0.5",
    }),
  notificar_cliente: z.boolean(),
});

export type TaskSchemaValues = z.infer<typeof taskSchema>;
