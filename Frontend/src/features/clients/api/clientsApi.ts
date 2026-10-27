import { api } from "@/shared/api/client";
import { ApiError, type ApiResponse } from "@/shared/api/types";
import type {
  AccountantOption,
  ClienteCreatePayload,
  ClienteDetalle,
  ClienteListItem,
  ClientesPage,
  ClientesQuery,
} from "../types";

const PER_PAGE_DEFAULT = 20;
const MAX_PAGES = 50;

function queryParams(filters: ClientesQuery) {
  return {
    q: filters.q.trim() || undefined,
    estatus: filters.estatus,
    tipo_persona: filters.tipo_persona ?? undefined,
    contador: filters.contador,
    page: filters.page,
  };
}

async function fetchPage(filters: ClientesQuery): Promise<ClientesPage> {
  const res = await api.get<ApiResponse<ClienteListItem[]>>("/clients", {
    params: queryParams(filters),
  });

  const items = res.data.data ?? [];
  const meta = res.data.meta ?? {
    page: filters.page,
    per_page: PER_PAGE_DEFAULT,
    total: items.length,
  };

  return { items, meta };
}

export const clientsApi = {
  list: fetchPage,

  /** Descarga el padrón completo (todas las páginas) para exportación. */
  async listAll(filters: ClientesQuery): Promise<ClienteListItem[]> {
    const first = await fetchPage({ ...filters, page: 1 });
    const pages = Math.min(
      first.meta.pages ?? Math.ceil(first.meta.total / (first.meta.per_page || PER_PAGE_DEFAULT)),
      MAX_PAGES,
    );
    const items = [...first.items];

    for (let page = 2; page <= pages; page += 1) {
      const next = await fetchPage({ ...filters, page });
      items.push(...next.items);
    }

    return items;
  },

  async create(payload: ClienteCreatePayload): Promise<ClienteDetalle> {
    const res = await api.post<ApiResponse<ClienteDetalle>>("/clients", payload);
    return res.data.data;
  },

  /**
   * HU_13. El backend todavía no publica este endpoint; cuando exista, el
   * expediente se alimentará de aquí sin cambiar la vista.
   */
  async get(id: number): Promise<ClienteDetalle> {
    const res = await api.get<ApiResponse<ClienteDetalle>>(`/clients/${id}`);
    return res.data.data;
  },

  async listAccountants(): Promise<AccountantOption[]> {
    const res = await api.get<ApiResponse<AccountantOption[]>>("/users", {
      params: { rol: "CONTADOR", estatus: "ACTIVO", page: 1 },
    });
    return res.data.data ?? [];
  },
};

/** El endpoint de detalle aún no existe: no debe tratarse como error de la vista. */
export function isDetailUnavailable(error: unknown): boolean {
  return error instanceof ApiError && [404, 405, 501].includes(error.status);
}
