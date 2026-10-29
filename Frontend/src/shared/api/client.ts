import axios, { AxiosError } from "axios";
import {ApiError, type ApiErrorBody} from "./types";
import { useAuthStore } from "../../shared/auth/authStore";


export const api = axios.create({
    baseURL: import.meta.env.VITE_API_URL ?? "/api/v1",
    withCredentials: true, //Envia/recibe las cookies httpOnly del jwt
});

const SAFE_METHODS = ["GET", "HEAD", "OPTIONS"];

function getCookie(name:string){
    return document.cookie
    .split(";")
    .find((c)=> c.startsWith(`${name}=`))
    ?.split("=")[1];
}

api.interceptors.request.use((config)=> {
    const method = config.method?.toUpperCase() ?? "GET";
    if (!SAFE_METHODS.includes(method)){
        const csrf = getCookie("csrf_access_token");
        if (csrf) config.headers.set("X-CSRF-TOKEN", csrf);
    }

    return config;
});

api.interceptors.response.use(
  (res) => res,
  (err: AxiosError<ApiErrorBody>) => {
    const status = err.response?.status ?? 0;
    const body = err.response?.data?.error;
    const headerRetry = Number(err.response?.headers?.["retry-after"]);

    // 401 fuera del login = sesión vencida: limpiar y los guards redirigen a /login
    if (status === 401 && !err.config?.url?.includes("/auth/login")) {
      useAuthStore.getState().clear();
    }

    return Promise.reject(
      new ApiError(
        status,
        body?.code ?? "NETWORK_ERROR",
        body?.message ?? "No se pudo conectar con el servidor",
        body?.fields,
        body?.retry_after ?? (Number.isFinite(headerRetry) ? headerRetry : undefined),
      ),
    );
  },
);