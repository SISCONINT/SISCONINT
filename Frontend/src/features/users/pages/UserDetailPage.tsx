import { useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { Pencil, ShieldOff } from "lucide-react";
import { PageHeader } from "@/shared/components/PageHeader";
import { Avatar } from "@/shared/components/Avatar";
import { EstatusBadge } from "@/shared/components/Badge";
import { formatDate } from "@/shared/utils/format";
import { useAuthStore } from "@/shared/auth/authStore";
import { ROLE_LABELS } from "@/shared/constants/roles";
import { useUpdateUser, useUser } from "../api/useUsers";
import { UserForm } from "../components/UserForm";
import { DeactivateDialog } from "../components/DeactivateDialog";
import { colaboradorToFormValues, GRADO_LABELS } from "../types";
import { canActorEditTarget } from "../permissions";

export function UserDetailPage() {
  const { id } = useParams();
  const userId = Number(id);
  const navigate = useNavigate();
  const actor = useAuthStore((s) => s.user);
  const [editing, setEditing] = useState(false);
  const [deactivating, setDeactivating] = useState(false);

  const { data: user, isLoading, isError } = useUser(userId);
  const { mutate, isPending, error } = useUpdateUser(userId);

  if (isLoading) return <p className="text-sm text-muted">Cargando ficha…</p>;
  if (isError || !user) return <p className="text-sm text-danger">No se encontró al colaborador.</p>;

  const canEdit = actor ? canActorEditTarget(actor.rol, user.rol) : false;

  const dato = (label: string, value?: string | null) => (
    <div>
      <p className="text-[11px] font-semibold uppercase tracking-wide text-muted">{label}</p>
      <p className="mt-0.5 text-sm text-ink">{value || "—"}</p>
    </div>
  );

  return (
    <div>
      <PageHeader
        title={editing ? "Editar colaborador" : "Ficha del colaborador"}
        crumbs={[{ label: "Colaboradores", to: "/colaboradores" }, { label: user.nombre_completo }]}
        actions={
          !editing && (
            <div className="flex gap-2">
              {canEdit && (
                <button
                  type="button"
                  onClick={() => setEditing(true)}
                  className="flex items-center gap-2 rounded-lg border border-line px-4 py-2.5 text-sm font-medium text-ink hover:bg-field"
                >
                  <Pencil size={15} /> Editar
                </button>
              )}
              {canEdit && user.estatus === "ACTIVO" && (
                <button
                  type="button"
                  onClick={() => setDeactivating(true)}
                  className="flex items-center gap-2 rounded-lg bg-red-50 px-4 py-2.5 text-sm font-semibold text-danger hover:brightness-95"
                >
                  <ShieldOff size={15} /> Desactivar
                </button>
              )}
            </div>
          )
        }
      />

      {!canEdit && (
        <p className="mb-4 rounded-lg bg-field px-3 py-2 text-sm text-muted">
          No puedes editar a un Dueño o Administrador (RG_08).
        </p>
      )}

      {editing ? (
        <div className="card p-5">
          <UserForm
            defaultValues={colaboradorToFormValues(user)}
            submitLabel="Guardar cambios"
            pending={isPending}
            serverError={error}
            onCancel={() => setEditing(false)}
            onSubmit={(values) => mutate(values, { onSuccess: () => setEditing(false) })}
          />
        </div>
      ) : (
        <div className="card p-5">
          <div className="mb-5 flex items-center gap-3">
            <Avatar nombre={user.nombre_completo} size={48} />
            <div>
              <p className="font-display text-lg font-bold text-ink">{user.nombre_completo}</p>
              <p className="text-sm text-muted">
                {ROLE_LABELS[user.rol]} · {GRADO_LABELS[user.grado_escalafon]}
              </p>
            </div>
            <span className="ml-auto">
              <EstatusBadge estatus={user.estatus} />
            </span>
          </div>

          <div className="grid grid-cols-1 gap-4 border-t border-line pt-4 sm:grid-cols-2 lg:grid-cols-3">
            {dato("Correo institucional", user.correo_institucional)}
            {dato("Teléfono del despacho", user.telefono_despacho)}
            {dato("Teléfono personal", user.telefono_personal)}
            {dato("Licenciatura", user.licenciatura)}
            {dato("Cédula profesional", user.cedula)}
            {dato("Fecha de alta", formatDate(user.fecha_alta))}
          </div>

          <div className="mt-5 border-t border-line pt-4">
            <h3 className="mb-3 text-[11px] font-semibold uppercase tracking-wide text-muted">Domicilio</h3>
            <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
              {dato("Calle y número", [user.calle, user.no_ext_int].filter(Boolean).join(" "))}
              {dato("Colonia", user.colonia)}
              {dato("Municipio", user.municipio)}
              {dato("Estado", user.estado)}
            </div>
          </div>

          <div className="mt-5 border-t border-line pt-4">
            <h3 className="mb-3 text-[11px] font-semibold uppercase tracking-wide text-muted">Contacto de emergencia</h3>
            <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
              {dato("Nombre", user.emergencia_nombre)}
              {dato("Teléfono", user.emergencia_telefono)}
            </div>
          </div>
        </div>
      )}

      <DeactivateDialog
        userId={userId}
        nombre={user.nombre_completo}
        open={deactivating}
        onClose={() => setDeactivating(false)}
        onDeactivated={() => navigate("/colaboradores")}
      />
    </div>
  );
}
