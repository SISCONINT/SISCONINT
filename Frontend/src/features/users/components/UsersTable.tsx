import { Link } from "react-router-dom";
import { Pencil } from "lucide-react";
import { DataTable, type Column } from "@/shared/components/DataTable";
import { canEditCollaborator } from "@/shared/auth/permissions";
import { ROLE_LABELS, type Role } from "@/shared/constants/roles";
import { GRADO_LABELS } from "@/shared/constants/grados";
import type { Colaborador } from "../types";

function columnsFor(actorRol: Role): Column<Colaborador>[] {
  return [
    { header: "Nombre", cell: (u) => <span className="font-semibold text-ink">{u.nombre_completo}</span> },
    { header: "Correo", cell: (u) => u.correo_institucional },
    { header: "Rol", cell: (u) => ROLE_LABELS[u.rol] },
    { header: "Grado escalafón", cell: (u) => GRADO_LABELS[u.grado_escalafon] },
    {
      header: "Estatus",
      cell: (u) => (
        <span
          className={`rounded-full px-2.5 py-0.5 text-[11px] font-bold ${
            u.estatus === "ACTIVO" ? "bg-green-100 text-green-800" : "bg-gray-200 text-gray-700"
          }`}
        >
          {u.estatus === "ACTIVO" ? "Activo" : "Inactivo"}
        </span>
      ),
    },
    {
      header: "Acciones",
      cell: (u) => (
        <Link
          to={`/colaboradores/${u.id}`}
          className="inline-flex items-center gap-1.5 text-sm font-semibold text-navy-800 hover:underline"
        >
          <Pencil size={14} />
          {canEditCollaborator(actorRol, u.rol) ? "Editar" : "Ver ficha"}
        </Link>
      ),
    },
  ];
}

interface Props {
  rows: Colaborador[];
  isLoading: boolean;
  dimmed: boolean;
  actorRol: Role;
}

export function UsersTable({ rows, isLoading, dimmed, actorRol }: Props) {
  return (
    <DataTable
      columns={columnsFor(actorRol)}
      rows={rows}
      getRowKey={(u) => u.id}
      isLoading={isLoading}
      dimmed={dimmed}
      emptyMessage="No hay colaboradores con los filtros seleccionados"
    />
  );
}