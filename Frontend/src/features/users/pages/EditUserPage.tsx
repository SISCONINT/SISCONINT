import { Link, useParams } from "react-router-dom";
import { ArrowLeft } from "lucide-react";
import { ApiError } from "@/shared/api/types";
import { useAuthStore } from "@/shared/auth/authStore";
import { canEditCollaborator } from "@/shared/auth/permissions";
import { GRADO_LABELS } from "@/shared/constants/grados";
import { ROLE_LABELS, ROLES } from "@/shared/constants/roles";
import { useActiveDuenoCount } from "../api/useActiveDuenoCount";
import { useUser } from "../api/useUser";
import { UserForm } from "../components/UserForm";

export function EditUserPage() {
  const { id } = useParams();
  const userId = Number(id);
  const validId = Number.isInteger(userId) && userId > 0;
  const actor = useAuthStore((s) => s.user);
  const { data, isPending, error } = useUser(validId ? userId : undefined);
  const isDuenoActivo = data?.rol === ROLES.DUENO && data.estatus === "ACTIVO";
  const { data: duenoCount } = useActiveDuenoCount(!!isDuenoActivo);
  const lastActiveOwner = !!isDuenoActivo && duenoCount !== undefined && duenoCount <= 1;
  const readOnly = !!data && !!actor && !canEditCollaborator(actor.rol, data.rol);

  return (
    <div className="mx-auto flex max-w-4xl flex-col gap-5">
      <header className="flex flex-col gap-3">
        <Link to="/colaboradores" className="inline-flex items-center gap-1.5 text-sm font-medium text-muted hover:text-ink">
          <ArrowLeft size={16} /> Volver a colaboradores
        </Link>
        <div>
          <h1 className="font-display text-2xl font-bold text-ink">
            {data?.nombre_completo ?? "Ficha del colaborador"}
          </h1>
          <p className="mt-1 text-sm text-muted">
            {readOnly
              ? "No puedes modificar a un usuario con este rol."
              : "Los cambios se reflejan de inmediato en esta ficha."}
          </p>
        </div>
      </header>

      {!validId || error ? (
        <p role="alert" className="card px-4 py-8 text-center text-sm font-medium text-danger">
          {error instanceof ApiError ? error.message : "Colaborador no encontrado"}
        </p>
      ) : isPending || !data ? (
        <p className="card px-4 py-8 text-center text-sm text-muted">Cargando ficha…</p>
      ) : (
        <>
          <section className="card flex flex-wrap items-center gap-3 p-4 text-sm">
            <span className="font-semibold text-ink">{data.correo_institucional}</span>
            <span className="rounded-full bg-navy-900/5 px-2.5 py-0.5 text-[11px] font-bold text-navy-800">
              {ROLE_LABELS[data.rol]}
            </span>
            <span className="rounded-full bg-navy-900/5 px-2.5 py-0.5 text-[11px] font-bold text-navy-800">
              {GRADO_LABELS[data.grado_escalafon]}
            </span>
            <span
              className={`rounded-full px-2.5 py-0.5 text-[11px] font-bold ${
                data.estatus === "ACTIVO" ? "bg-green-100 text-green-800" : "bg-gray-200 text-gray-700"
              }`}
            >
              {data.estatus === "ACTIVO" ? "Activo" : "Inactivo"}
            </span>
          </section>
          <UserForm colaborador={data} lastActiveOwner={lastActiveOwner} readOnly={readOnly} />
        </>
      )}
    </div>
  );
}
