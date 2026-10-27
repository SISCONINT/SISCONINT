import { z } from "zod";

export const passwordSchema = z
  .string()
  .min(1, "Campo obligatorio")
  .min(10, "Mínimo 10 caracteres")
  .regex(/[A-Z]/, "Debe incluir una mayúscula")
  .regex(/[a-z]/, "Debe incluir una minúscula")
  .regex(/\d/, "Debe incluir un número")
  .regex(/[^A-Za-z0-9]/, "Debe incluir un símbolo");