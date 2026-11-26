import { Link, useNavigate, useParams } from "react-router-dom";
import { AlertTriangle, Pencil } from "lucide-react";
import { useClientDetail } from "../api/useClients";
import { clienteToFormValues } from "../schemas/client.schema";
import { ClientForm } from "../components/form/ClientForm";
import { BTN_SECONDARY } from "../constants";

export function EditClientPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const clientId = Number(id);
  const validId = Number.isInteger(clientId) && clientId > 0;

  const detailQuery = useClientDetail(clientId, validId);

  if (!validId) {
    return (
      <div className="card mx-auto flex max-w-lg flex-col items-center gap-3 px-6 py-12 text-center">
        <span className="grid size-12 place-items-center rounded-full bg-red-50 text-danger">
          <AlertTriangle size={22} />
        </span>
        <h1 className="font-display text-lg font-bold text-ink">Cliente no válido</h1>
        <Link to="/clientes" className={BTN_SECONDARY}>
          Volver a la cartera
        </Link>
      </div>
    );
  }

  if (detailQuery.isLoading) {
    return (
      <div className="mx-auto w-full max-w-5xl" aria-busy="true">
        <div className="card h-40 animate-pulse" />
      </div>
    );
  }

  if (!detailQuery.data) {
    return (
      <div className="card mx-auto flex max-w-xl flex-col items-center gap-3 px-6 py-12 text-center">
        <span className="grid size-12 place-items-center rounded-full bg-red-50 text-danger">
          <AlertTriangle size={22} />
        </span>
        <h1 className="font-display text-lg font-bold text-ink">No se pudo abrir el cliente</h1>
        <p className="text-sm text-muted">
          {detailQuery.error instanceof Error ? detailQuery.error.message : "Ocurrió un error inesperado."}
        </p>
        <div className="flex gap-2">
          <button type="button" onClick={() => navigate(-1)} className={BTN_SECONDARY}>
            Volver
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="mx-auto flex w-full max-w-5xl flex-col gap-4">
      <header>
        <nav aria-label="Ruta de navegación" className="mb-1 flex flex-wrap items-center gap-1.5 text-[11px] text-muted">
          <Link to="/clientes" className="transition hover:text-navy-800">
            Clientes
          </Link>
          <span aria-hidden="true">/</span>
          <Link to={`/clientes/${clientId}`} className="transition hover:text-navy-800">
            {detailQuery.data.nombre_completo}
          </Link>
          <span aria-hidden="true">/</span>
          <span className="font-semibold text-navy-800">Editar</span>
        </nav>

        <div className="flex items-center gap-2">
          <Pencil size={18} className="text-gold-700" />
          <h1 className="font-display text-2xl font-bold leading-tight text-ink sm:text-3xl">
            Editar expediente de {detailQuery.data.nombre_completo}
          </h1>
        </div>
        <p className="mt-1.5 max-w-2xl text-sm text-muted">
          HU_14: actualiza los datos generales, domicilio fiscal, régimen y contactos del contribuyente.
        </p>
      </header>

      <ClientForm clientId={clientId} initialValues={clienteToFormValues(detailQuery.data)} />
    </div>
  );
}
