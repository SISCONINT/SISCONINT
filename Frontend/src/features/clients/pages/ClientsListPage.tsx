import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { Search, UserPlus, Users as ClientsIcon } from "lucide-react";
import { PageHeader } from "@/shared/components/PageHeader";
import { EmptyState } from "@/shared/components/EmptyState";
import { Pagination } from "@/shared/components/Pagination";
import { inputClass } from "@/shared/components/FormField";
import { useDebouncedValue } from "@/shared/hooks/useDebouncedValue";
import { useAuthStore } from "@/shared/auth/authStore";
import { ROLES } from "@/shared/constants/roles";
import { useClients } from "../api/useClients";
import { ClientTable } from "../components/ClientTable";
import type { ClienteEstatus } from "../types";

export function ClientsListPage() {
  const navigate = useNavigate();
  const actor = useAuthStore((s) => s.user);
  const canCreate = actor && (actor.rol === ROLES.DUENO || actor.rol === ROLES.ADMINISTRADOR);

  const [q, setQ] = useState("");
  const [estatus, setEstatus] = useState<ClienteEstatus>("ACTIVO");
  const [page, setPage] = useState(1);
  const debouncedQ = useDebouncedValue(q);

  const { data, isLoading, isError } = useClients({ q: debouncedQ || undefined, estatus, page });
  const items = data?.data ?? [];
  const meta = data?.meta;

  return (
    <div>
      <PageHeader
        title="Clientes"
        subtitle="Expediente fiscal de cada cliente del despacho."
        actions={
          canCreate && (
            <button
              type="button"
              onClick={() => navigate("/clientes/nuevo")}
              className="flex items-center gap-2 rounded-lg bg-gold-300 px-4 py-2.5 text-sm font-semibold text-ink hover:brightness-95"
            >
              <UserPlus size={16} /> Nuevo cliente
            </button>
          )
        }
      />

      <div className="card">
        <div className="flex flex-wrap items-center gap-3 border-b border-line p-4">
          <div className="relative min-w-[220px] flex-1">
            <Search size={16} className="pointer-events-none absolute left-3.5 top-1/2 -translate-y-1/2 text-muted" />
            <input
              value={q}
              onChange={(e) => {
                setQ(e.target.value);
                setPage(1);
              }}
              placeholder="Buscar por nombre o RFC…"
              className={inputClass + " pl-10"}
            />
          </div>
          <select
            value={estatus}
            onChange={(e) => {
              setEstatus(e.target.value as ClienteEstatus);
              setPage(1);
            }}
            className="rounded-lg bg-field px-3 py-2.5 text-sm text-ink outline-none"
          >
            <option value="ACTIVO">Activos</option>
            <option value="PAUSADO">Pausados</option>
            <option value="BAJA">Baja</option>
          </select>
        </div>

        {isLoading ? (
          <p className="p-6 text-sm text-muted">Cargando clientes…</p>
        ) : isError ? (
          <p className="p-6 text-sm text-danger">No se pudo cargar la lista.</p>
        ) : items.length === 0 ? (
          <EmptyState icon={ClientsIcon} title="Sin clientes" description="No hay registros con estos filtros." />
        ) : (
          <>
            <div className="overflow-x-auto">
              <ClientTable items={items} />
            </div>
            {meta && (
              <Pagination page={meta.page} pages={meta.pages ?? 1} total={meta.total} perPage={meta.per_page} onChange={setPage} />
            )}
          </>
        )}
      </div>
    </div>
  );
}
