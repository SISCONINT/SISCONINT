import { useState } from "react";
import { Link } from "react-router-dom";
import { UserPlus } from "lucide-react";
import { Pagination } from "@/shared/components/Pagination";
import { useDebounce } from "@/shared/hooks/useDebounce";
import { ApiError } from "@/shared/api/types";
import { useAuthStore } from "@/shared/auth/authStore";
import { ROLES } from "@/shared/constants/roles";
import { useUsers } from "../api/useUsers";
import { UsersFilters } from "../components/UsersFilters";
import { UsersTable } from "../components/UsersTable";
import type { UsersFilters as Filters } from "../types";

const PER_PAGE = 20; // RG-07

export function UsersListPage() {
  const actorRol = useAuthStore((s) => s.user?.rol);
  const [searchInput, setSearchInput] = useState("");
  const [filters, setFilters] = useState<Omit<Filters, "search">>({
    rol: "",
    estatus: "ACTIVO", // por defecto solo Activos
    page: 1,
  });

  const search = useDebounce(searchInput.trim(), 400);
  const { data, isPending, isFetching, isPlaceholderData, error } = useUsers({ ...filters, search });

  // Cualquier cambio de filtro regresa a la página 1
  const update = (patch: Partial<Omit<Filters, "search" | "page">>) =>
    setFilters((f) => ({ ...f, ...patch, page: 1 }));

  return (
    <div className="flex flex-col gap-5">
      <header className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="font-display text-2xl font-bold text-ink">Colaboradores</h1>
          <p className="mt-1 text-sm text-muted">
            {data ? `${data.meta.total} colaboradores` : "Integrantes del despacho"}
          </p>
        </div>
        <Link
          to="/colaboradores/nuevo"
          className="inline-flex items-center gap-2 rounded-lg bg-gold-300 px-4 py-2.5 text-sm font-semibold text-ink hover:brightness-95"
        >
          <UserPlus size={16} /> Registrar colaborador
        </Link>
      </header>

      <section className="card">
        <UsersFilters
          search={searchInput}
          rol={filters.rol}
          estatus={filters.estatus}
          onSearchChange={(v) => { setSearchInput(v); setFilters((f) => ({ ...f, page: 1 })); }}
          onRolChange={(rol) => update({ rol })}
          onEstatusChange={(estatus) => update({ estatus })}
        />

        {error ? (
          <p role="alert" className="px-4 py-8 text-center text-sm font-medium text-danger">
            {error instanceof ApiError ? error.message : "No se pudo cargar la lista."}
          </p>
        ) : (
          <>
            <UsersTable
              rows={data?.data ?? []}
              isLoading={isPending}
              dimmed={isFetching && isPlaceholderData}
              actorRol={actorRol ?? ROLES.ADMINISTRADOR}
            />
            {data && (
              <Pagination
                page={data.meta.page}
                perPage={PER_PAGE}
                total={data.meta.total}
                onChange={(page) => setFilters((f) => ({ ...f, page }))}
              />
            )}
          </>
        )}
      </section>
    </div>
  );
}