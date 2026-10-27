import { z } from "zod";
import { passwordSchema } from "./password.schema";

export const activateSchema = z
  .object({
    password: passwordSchema,
    confirmacion: z.string().min(1, "Campo obligatorio"),
  })
  .refine((d) => d.password === d.confirmacion, {
    path: ["confirmacion"], // el error se muestra bajo este campo
    message: "Las contraseñas no coinciden",
  });

export type ActivateFormValues = z.infer<typeof activateSchema>;