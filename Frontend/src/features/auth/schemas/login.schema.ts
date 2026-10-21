import { z } from "zod";

export const loginSchema = z.object({
  correo: z.string().min(1, "Campo obligatorio").email("Correo con formato inválido"),
  // En login solo se exige que exista: la política RG-05 se valida al CREAR la contraseña
  password: z.string().min(1, "Campo obligatorio"),
  recordar: z.boolean(),
});

export type LoginFormValues = z.infer<typeof loginSchema>;