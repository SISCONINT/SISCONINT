import { api } from "@/shared/api/client";
import { ApiError, type ApiResponse } from "../../../shared/api/types";
import type { AuthUser } from "@/shared/auth/authStore";
import type { Role } from "@/shared/constants/roles";

interface RawUser {
  id: number;
  nombre_completo: string;
  rol: Role;
}

// Tolera { data: { user } } o { data: {...usuario} }
const toAuthUser = (data: RawUser | { user: RawUser }): AuthUser => {
  const u = "user" in data ? data.user : data;
  return { id: u.id, nombre: u.nombre_completo, rol: u.rol };
};

export const authApi = {
  login: async (p: { correo: string; password: string }) => {
    const res = await api.post<ApiResponse<RawUser | { user: RawUser }>>("/auth/login", {
      correo_institucional: p.correo,
      password: p.password,
    });
    return toAuthUser(res.data.data);
  },

  me: async () => {
    const res = await api.get<ApiResponse<RawUser | { user: RawUser }>>("/auth/me");
    return toAuthUser(res.data.data);
  },

  logout: async () => {
  try{
    await api.post("/auth/logout");
  } catch (e){
    if (e instanceof ApiError && e.status === 401) return;
    throw e;
  }
  },

  activate: async (p: { token: string; password: string; password_confirm: string }) => {
    await api.post("/auth/activate", {
      token: p.token,
      password: p.password,
      password_confirm: p.password_confirm,
    });
  },
};