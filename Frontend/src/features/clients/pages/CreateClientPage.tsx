import { Link } from "react-router-dom";
import { ShieldCheck } from "lucide-react";
import { ClientForm } from "../components/form/ClientForm";

export function CreateClientPage() {
  return (
    <div className="mx-auto flex w-full max-w-5xl flex-col gap-4">
      <header>
        <nav aria-label="Ruta de navegación" className="mb-1 flex flex-wrap items-center gap-1.5 text-[11px] text-muted">
          <Link to="/clientes" className="transition hover:text-navy-800">
            Clientes
          </Link>
          <span aria-hidden="true">/</span>
          <span className="font-semibold text-navy-800">Alta de contribuyente</span>
        </nav>

        <div className="flex flex-col gap-2 sm:flex-row sm:items-start sm:justify-between">
          <div>
            <p className="text-[10px] font-semibold uppercase tracking-[0.16em] text-gold-700">
              Expediente fiscal · HU_11
            </p>
            <h1 className="mt-1 font-display text-2xl font-bold leading-tight text-ink sm:text-3xl">
              Registro de Nuevo Contribuyente
            </h1>
            <p className="mt-1.5 max-w-2xl text-sm text-muted">
              Captura integral del expediente fiduciario, situación fiscal ante el SAT y
              asignación del contador responsable.
            </p>
          </div>

          <span className="inline-flex w-fit items-center gap-1.5 rounded-lg border border-line bg-surface px-3 py-2 text-[11px] font-semibold text-navy-800">
            <ShieldCheck size={15} className="text-gold-700" />
            Validación fiscal activa
          </span>
        </div>
      </header>

      <div className="flex items-start gap-2 rounded-lg bg-navy-900/[0.04] px-4 py-2.5 text-[11px] leading-relaxed text-navy-800">
        <span className="mt-0.5 font-bold text-gold-700">*</span>
        Los campos marcados con asterisco son obligatorios. El RFC y el contador asignado se
        validan nuevamente en el servidor al guardar el expediente.
      </div>

      <ClientForm />
    </div>
  );
}
