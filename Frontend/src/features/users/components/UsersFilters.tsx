import { Search } from "lucide-react";
import { plainInputClass } from "@/shared/components/FormField";
import { ROLES, ROLE_LABELS, type Role } from "@/shared/constants/roles";
import type { EstatusColaborador } from "../types";

interface Props {
  search: string;
  rol: Role | "";
  estatus: EstatusColaborador | "";
  onSearchChange: (v: string) => void;
  onRolChange: (v: Role | "") => void;
  onEstatusChange: (v: EstatusColaborador | "") => void;
}

export function UsersFilters({ search, rol, estatus, onSearchChange, onRolChange, onEstatusChange }: Props) {
  return (
    <div className="grid gap-3 p-4 sm:grid-cols-[1fr_12rem_12rem]">
      <div className="relative">
        <label htmlFor="users-search" className="sr-only">Buscar colaborador</label>
        <Search size={16} className="pointer-events-none absolute left-3.5 top-1/2 -translate-y-1/2 text-muted" />
        <input
          id="users-search"
          type="search"
          value={search}
          onChange={(e) => onSearchChange(e.target.value)}
          placeholder="Buscar por nombre o correo"
          className={`${plainInputClass} pl-10`}
        />
      </div>

      <div>
        <label htmlFor="users-rol" className="sr-only">Filtrar por rol</label>
        <select id="users-rol" value={rol} onChange={(e) => onRolChange(e.target.value as Role | "")} className={plainInputClass}>
          <option value="">Todos los roles</option>
          {Object.values(ROLES).map((r) => (
            <option key={r} value={r}>{ROLE_LABELS[r]}</option>
          ))}
        </select>
      </div>

      <div>
        <label htmlFor="users-estatus" className="sr-only">Filtrar por estatus</label>
        <select
          id="users-estatus"
          value={estatus}
          onChange={(e) => onEstatusChange(e.target.value as EstatusColaborador | "")}
          className={plainInputClass}
        >
          <option value="ACTIVO">Activos</option>
          <option value="INACTIVO">Inactivos</option>
          <option value="">Todos</option>
        </select>
      </div>
    </div>
  );
}