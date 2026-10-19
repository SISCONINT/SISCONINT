import { ApiError } from "../../shared/api/types";

export function loginErrorMessage(e: unknown): string {
  if (!(e instanceof ApiError)) return "Ocurrió un error inesperado. Intenta de nuevo.";
  switch (e.status) {
    case 401: return "Correo o contraseña incorrectos";
    case 403: return "Cuenta desactivada. Contacta al Administrador";
    case 429: return "Demasiadas solicitudes. Espera un momento e intenta de nuevo.";
    case 0:   return "No se pudo conectar con el servidor.";
    default:  return e.message;
  }
}