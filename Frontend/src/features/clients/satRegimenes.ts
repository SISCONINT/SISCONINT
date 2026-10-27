/**
 * Catálogo SAT c_RegimenFiscal (RESICO, Ley de Ingresos vigente). El backend tiene el
 * catálogo real en la tabla `regimen_fiscal`, pero no expone un endpoint para leerlo, así
 * que aquí se usa una copia estática de referencia solo para mostrar la descripción de
 * cada clave: el backend sigue siendo quien valida qué claves existen.
 */
export interface RegimenRef {
  clave: string;
  descripcion: string;
  aplicaFisica: boolean;
  aplicaMoral: boolean;
}

export const REGIMENES: RegimenRef[] = [
  { clave: "601", descripcion: "General de Ley Personas Morales", aplicaFisica: false, aplicaMoral: true },
  { clave: "603", descripcion: "Personas Morales con Fines no Lucrativos", aplicaFisica: false, aplicaMoral: true },
  { clave: "605", descripcion: "Sueldos y Salarios e Ingresos Asimilados a Salarios", aplicaFisica: true, aplicaMoral: false },
  { clave: "606", descripcion: "Arrendamiento", aplicaFisica: true, aplicaMoral: false },
  { clave: "608", descripcion: "Demás ingresos", aplicaFisica: true, aplicaMoral: false },
  { clave: "609", descripcion: "Consolidación", aplicaFisica: false, aplicaMoral: true },
  { clave: "610", descripcion: "Residentes en el Extranjero sin Establecimiento Permanente", aplicaFisica: true, aplicaMoral: true },
  { clave: "611", descripcion: "Ingresos por Dividendos (socios y accionistas)", aplicaFisica: true, aplicaMoral: false },
  { clave: "612", descripcion: "Personas Físicas con Actividades Empresariales y Profesionales", aplicaFisica: true, aplicaMoral: false },
  { clave: "614", descripcion: "Ingresos por intereses", aplicaFisica: true, aplicaMoral: false },
  { clave: "615", descripcion: "Ingresos por obtención de premios", aplicaFisica: true, aplicaMoral: false },
  { clave: "616", descripcion: "Sin obligaciones fiscales", aplicaFisica: true, aplicaMoral: false },
  { clave: "620", descripcion: "Sociedades Cooperativas de Producción", aplicaFisica: false, aplicaMoral: true },
  { clave: "621", descripcion: "Incorporación Fiscal", aplicaFisica: true, aplicaMoral: false },
  { clave: "622", descripcion: "Actividades Agrícolas, Ganaderas, Silvícolas y Pesqueras", aplicaFisica: true, aplicaMoral: true },
  { clave: "623", descripcion: "Opcional para Grupos de Sociedades", aplicaFisica: false, aplicaMoral: true },
  { clave: "624", descripcion: "Coordinados", aplicaFisica: false, aplicaMoral: true },
  { clave: "625", descripcion: "Actividades Empresariales con ingresos a través de Plataformas Tecnológicas", aplicaFisica: true, aplicaMoral: false },
  { clave: "626", descripcion: "Régimen Simplificado de Confianza (RESICO)", aplicaFisica: true, aplicaMoral: false },
];

export function regimenesPara(tipo: "FISICA" | "MORAL"): RegimenRef[] {
  return REGIMENES.filter((r) => (tipo === "FISICA" ? r.aplicaFisica : r.aplicaMoral));
}

export function regimenLabel(clave: string): string {
  const r = REGIMENES.find((x) => x.clave === clave);
  return r ? `${r.clave} · ${r.descripcion}` : clave;
}
