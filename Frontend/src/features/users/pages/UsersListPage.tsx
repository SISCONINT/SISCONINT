import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { Search, UserPlus, Users as UsersIcon } from "lucide-react";
import { PageHeader } from "@/shared/components/PageHeader";
import { EmptyState } from "@/shared/components/EmptyState";
import { Pagination } from "@/shared/components/Pagination";
import { inputClass } from "@/shared/components/FormField";
import { useDebouncedValue } from "@/shared/hooks/useDebouncedValue";
import { ROLES, ROLE_LABELS, type Role } from "@/shared/constants/roles";
import { useUsers } from "../api/useUsers";
import { UserTable } from "../components/UserTable";
import type { ColaboradorFilters } from "../types";

export function UsersListPage() {
  const navigate = useNavigate();
  const [q, setQ] = useState("");
  const [rol, setRol] = useState<Role | "">("");
  const [estatus, setEstatus] = useState<ColaboradorFilters["estatus"]>("ACTIVO");
  const [page, setPage] = useState(1);
  const debouncedQ = useDebouncedValue(q);

  const { data, isLoading, isError } = useUsers({
    q: debouncedQ || undefined,
    rol: rol || undefined,
    estatus,
    page,
  });

  const items = data?.data ?? [];
  const meta = data?.meta;

  return (
    <div>
      <PageHeader
        title="Colaboradores"
        subtitle="Alta, consulta y gestión del equipo del despacho (HU_05–HU_09)."
        actions={
          <button
            type="button"
            onClick={() => navigate("/colaboradores/nuevo")}
            className="flex items-center gap-2 rounded-lg bg-gold-300 px-4 py-2.5 text-sm font-semibold text-ink hover:brightness-95"
          >
            <UserPlus size={16} /> Nuevo colaborador
          </button>
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
              placeholder="Buscar por nombre o correo…"
              className={inputClass + " pl-10"}
            />
          </div>
          <select
            value={rol}
            onChange={(e) => {
              setRol(e.target.value as Role | "");
              setPage(1);
            }}
            className="rounded-lg bg-field px-3 py-2.5 text-sm text-ink outline-none"
          >
            <option value="">Todos los roles</option>
            {ROLES ? Object.values(ROLES).map((r) => (
              <option key={r} value={r}>
                {ROLE_LABELS[r]}
              </option>
            )) : null}
          </select>
          <select
            value={estatus}
            onChange={(e) => {
              setEstatus(e.target.value as ColaboradorFilters["estatus"]);
              setPage(1);
            }}
            className="rounded-lg bg-field px-3 py-2.5 text-sm text-ink outline-none"
          >
            <option value="ACTIVO">Activos</option>
            <option value="INACTIVO">Inactivos</option>
          </select>
        </div>

        {isLoading ? (
          <p className="p-6 text-sm text-muted">Cargando colaboradores…</p>
        ) : isError ? (
          <p className="p-6 text-sm text-danger">No se pudo cargar la lista.</p>
        ) : items.length === 0 ? (
          <EmptyState icon={UsersIcon} title="Sin colaboradores" description="No hay registros con estos filtros." />
        ) : (
          <>
            <div className="overflow-x-auto">
              <UserTable items={items} />
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
