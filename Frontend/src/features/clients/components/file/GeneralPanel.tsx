import { Landmark, MapPin, Wallet } from "lucide-react";
import {
  FORMA_PAGO_LABELS,
  TIPO_NOMINA_LABELS,
  TIPO_PERSONA_LABELS,
} from "../../constants";
import type { ClienteExpediente } from "../../types";
import { fullAddress } from "../../utils";
import { StatusBadge } from "../ClientBadges";
import { InfoTile } from "./InfoTile";
import { PanelCard } from "./PanelCard";

export function GeneralPanel({ cliente }: { cliente: ClienteExpediente }) {
  const contactoPrincipal = cliente.contactos?.find((contacto) => contacto.tipo === "PRINCIPAL");
  const direccion = fullAddress(cliente);

  return (
    <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-3">
      <PanelCard icon={Landmark} title="Datos de constitución">
        <div className="grid gap-2">
          <InfoTile label="Razón o denominación social" value={cliente.razon_social} />
          <InfoTile label="Nombre comercial / marca" value={cliente.nombre_completo} />
          <InfoTile
            label="RFC"
            value={<span className="tracking-wide">{cliente.rfc}</span>}
          />
          <InfoTile label="Tipo de persona" value={TIPO_PERSONA_LABELS[cliente.tipo_persona]} />
          <InfoTile label="Giro o actividad preponderante" value={cliente.giro} />
          <InfoTile label="Estatus en cartera" value={<StatusBadge estatus={cliente.estatus} />} />
        </div>
      </PanelCard>

      <PanelCard icon={MapPin} title="Domicilio fiscal" subtitle="Ubicación registrada ante el SAT">
        <div className="grid gap-2">
          <InfoTile label="Dirección registrada" value={direccion} />
          <div className="grid grid-cols-2 gap-2">
            <InfoTile label="Código postal" value={cliente.codigo_postal} />
            <InfoTile label="Colonia / asentamiento" value={cliente.colonia} />
            <InfoTile label="Municipio o alcaldía" value={cliente.ciudad} />
            <InfoTile label="Entidad federativa" value={cliente.estado} />
          </div>
          <InfoTile
            label="Referencias de ubicación"
            value={
              cliente.calle || cliente.no_exterior
                ? [cliente.calle, cliente.no_exterior && `No. ${cliente.no_exterior}`, cliente.no_interior && `Int. ${cliente.no_interior}`]
                    .filter(Boolean)
                    .join(" ")
                : null
            }
          />
        </div>
      </PanelCard>

      <PanelCard icon={Wallet} title="Convenio y recursos" subtitle="Contacto y esquema de nómina">
        <div className="grid gap-2">
          <InfoTile
            label="Forma de pago convenida"
            value={cliente.forma_pago ? FORMA_PAGO_LABELS[cliente.forma_pago] : null}
          />
          <InfoTile
            label="Contacto principal"
            value={contactoPrincipal?.nombre_completo ?? cliente.contacto_principal_correo}
            hint={contactoPrincipal?.cargo}
          />
          <div className="grid grid-cols-2 gap-2">
            <InfoTile label="Teléfono" value={cliente.telefono} />
            <InfoTile label="Correo" value={cliente.correo} />
          </div>
          <InfoTile
            label="Esquema laboral"
            value={
              cliente.tiene_trabajadores === undefined
                ? null
                : cliente.tiene_trabajadores
                  ? `Con trabajadores · ${cliente.tipo_nomina ? TIPO_NOMINA_LABELS[cliente.tipo_nomina] : "nómina"}`
                  : "Sin trabajadores / sin nómina"
            }
          />
        </div>
      </PanelCard>
    </div>
  );
}
