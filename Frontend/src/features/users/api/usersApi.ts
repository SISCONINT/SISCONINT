import { api } from "@/shared/api/client";
import type { ApiResponse } from "@/shared/api/types";
import type { RegisterUserFormValues } from "../schemas/user.schema";
import type { ColaboradorCreado } from "../types"

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
};

