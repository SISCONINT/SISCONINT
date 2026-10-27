import { api } from "@/shared/api/client";
import type { ApiResponse } from "@/shared/api/types";
import type { RegisterUserFormValues } from "../schemas/user.schema";
import type { Paginated } from "@/shared/api/types";
import type { Colaborador, ColaboradorCreado, UsersFilters } from "../types";

const omitEmpty = (values: object)=>
    Object.fromEntries(Object.entries(values).filter(([, value])=> value !== ""));

export const userApi = {
    create: async (values: RegisterUserFormValues)=>{
        const res = await api.post<ApiResponse<ColaboradorCreado>>(
            "/users",
            omitEmpty(values),
        );
        return res.data.data;
    },

    list: async (f: UsersFilters) => {
    const res = await api.get<Paginated<Colaborador>>("/users", {
      params: {
        page: f.page,
        ...(f.search && { search: f.search }),   // solo si no está vacío
        ...(f.rol && { rol: f.rol }),
        ...(f.estatus && { estatus: f.estatus }),
      },
    });
    return res.data; // { data: [...], meta: {...} }
  },

    get: async (id: number) => {
        const res = await api.get<ApiResponse<Colaborador>>(`/users/${id}`);
        return res.data.data;
    },

    update: async (id: number, values: RegisterUserFormValues) => {
        const res = await api.put<ApiResponse<Colaborador>>(
            `/users/${id}`,
            omitEmpty(values),
        );
        return res.data.data;
    },
};