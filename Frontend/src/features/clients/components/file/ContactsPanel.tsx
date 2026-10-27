import { Mail, Phone, UserRound, Wallet } from "lucide-react";
import type { ClienteExpediente } from "../../types";
import { InfoTile } from "./InfoTile";
import { PanelCard } from "./PanelCard";

export function ContactsPanel({ cliente }: { cliente: ClienteExpediente }) {
  const contactos = cliente.contactos ?? [];

  if (contactos.length === 0) {
    return (
      <div className="card flex flex-col items-center gap-3 px-6 py-12 text-center">
        <span className="grid size-12 place-items-center rounded-full bg-app text-navy-800">
          <UserRound size={22} />
        </span>
        <div>
          <h2 className="font-display text-base font-bold text-ink">Sin contactos en el expediente</h2>
          <p className="mt-1 max-w-md text-xs text-muted">
            {cliente.contacto_principal_correo
              ? `El padrón solo expone el correo ${cliente.contacto_principal_correo}. El directorio completo se mostrará al consultar el expediente.`
              : "El contribuyente no tiene contactos registrados."}
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="grid gap-3 lg:grid-cols-2">
      {contactos.map((contacto) => {
        const esPrincipal = contacto.tipo === "PRINCIPAL";
        return (
          <PanelCard
            key={contacto.id}
            icon={esPrincipal ? UserRound : Wallet}
            title={esPrincipal ? "Contacto principal / representante legal" : "Contacto de pagos y tesorería"}
            subtitle={contacto.cargo}
            aside={
              <span className="rounded-full bg-app px-2 py-0.5 text-[9.5px] font-semibold uppercase tracking-wider text-muted">
                {esPrincipal ? "Principal" : "Pagos"}
              </span>
            }
          >
            <div className="grid gap-2">
              <InfoTile label="Nombre completo" value={contacto.nombre_completo} />
              <div className="grid gap-2 sm:grid-cols-2">
                <InfoTile
                  label="Teléfono"
                  value={
                    <span className="inline-flex items-center gap-1.5">
                      <Phone size={12} className="text-muted" />
                      {contacto.telefono}
                    </span>
                  }
                />
                <InfoTile
                  label="Correo"
                  value={
                    <span className="inline-flex items-center gap-1.5 break-all">
                      <Mail size={12} className="shrink-0 text-muted" />
                      {contacto.correo}
                    </span>
                  }
                />
              </div>
            </div>
          </PanelCard>
        );
      })}
    </div>
  );
}
