import { create } from "zustand";
import type { Role } from "../../shared/constants/roles";

export interface AuthUser {
  id: number;
  nombre: string;
  rol: Role;
}

type AuthStatus = "checking" | "authenticated" | "anonymous";

interface AuthState {
  user: AuthUser | null;
  status: AuthStatus;
  setUser: (u: AuthUser) => void;
  clear: () => void;
}

export const useAuthStore = create<AuthState>((set) => ({
  user: null,
  status: "checking", // al abrir la app aún no sabemos si hay sesión
  setUser: (user) => set({ user, status: "authenticated" }),
  clear: () => set({ user: null, status: "anonymous" }),
}));