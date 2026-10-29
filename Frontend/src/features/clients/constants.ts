import type {
  EstatusCliente,
  FormaPago,
  TipoNomina,
  TipoPersona,
} from "./types";

export const ESTATUS_CLIENTE: EstatusCliente[] = ["ACTIVO", "PAUSADO", "BAJA"];

export const ESTATUS_LABELS: Record<EstatusCliente, string> = {
  ACTIVO: "Activo",
  PAUSADO: "Pausado",
  BAJA: "Baja",
};

export const ESTATUS_FILTER_LABELS: Record<EstatusCliente, string> = {
  ACTIVO: "Activos",
  PAUSADO: "Pausados",
  BAJA: "Bajas",
};

export const ESTATUS_BADGE: Record<EstatusCliente, string> = {
  ACTIVO: "bg-emerald-50 text-emerald-700 ring-emerald-200",
  PAUSADO: "bg-amber-50 text-amber-800 ring-amber-200",
  BAJA: "bg-slate-100 text-slate-600 ring-slate-200",
};

export const ESTATUS_DOT: Record<EstatusCliente, string> = {
  ACTIVO: "bg-emerald-500",
  PAUSADO: "bg-amber-500",
  BAJA: "bg-slate-400",
};

export const TIPO_PERSONA_LABELS: Record<TipoPersona, string> = {
  FISICA: "Persona física",
  MORAL: "Persona moral",
};

export const TIPO_PERSONA_OPTIONS: { value: TipoPersona; label: string }[] = [
  { value: "FISICA", label: "Persona física" },
  { value: "MORAL", label: "Persona moral" },
];

export const FORMA_PAGO_LABELS: Record<FormaPago, string> = {
  EFECTIVO: "Efectivo",
  TRANSFERENCIA: "Transferencia",
};

export const FORMA_PAGO_OPTIONS: { value: FormaPago; label: string }[] = [
  { value: "EFECTIVO", label: "Efectivo" },
  { value: "TRANSFERENCIA", label: "Transferencia" },
];

export const TIPO_NOMINA_LABELS: Record<TipoNomina, string> = {
  SEMANAL: "Semanal",
  QUINCENAL: "Quincenal",
  MENSUAL: "Mensual",
};

export const TIPO_NOMINA_OPTIONS: { value: TipoNomina; label: string }[] = [
  { value: "SEMANAL", label: "Semanal" },
  { value: "QUINCENAL", label: "Quincenal" },
  { value: "MENSUAL", label: "Mensual" },
];

export interface RegimenSat {
  clave: string;
  nombre: string;
  descripcion: string;
  aplica: TipoPersona[];
}

/**
 * Catálogo de regímenes fiscales del Anexo 20 del SAT.
 * El backend valida que la clave exista en la tabla `regimen_fiscal`.
 */
export const REGIMENES_SAT: RegimenSat[] = [
  {
    clave: "601",
    nombre: "General de Ley Personas Morales",
    descripcion: "ISR anual, pagos provisionales y obligaciones corporativas.",
    aplica: ["MORAL"],
  },
  {
    clave: "603",
    nombre: "Personas Morales con Fines no Lucrativos",
    descripcion: "Asociaciones civiles, donatarias autorizadas y colegios.",
    aplica: ["MORAL"],
  },
  {
    clave: "605",
    nombre: "Sueldos y Salarios e Ingresos Asimilados",
    descripcion: "Personas físicas con ingresos por trabajo subordinado.",
    aplica: ["FISICA"],
  },
  {
    clave: "606",
    nombre: "Arrendamiento",
    descripcion: "Personas físicas que otorgan el uso o goce temporal de bienes.",
    aplica: ["FISICA"],
  },
  {
    clave: "607",
    nombre: "Enajenación o Adquisición de Bienes",
    descripcion: "Operaciones de compraventa de bienes distintos de inmuebles.",
    aplica: ["FISICA"],
  },
  {
    clave: "608",
    nombre: "Demás ingresos",
    descripcion: "Ingresos no contemplados en otro régimen de personas físicas.",
    aplica: ["FISICA"],
  },
  {
    clave: "609",
    nombre: "Consolidación",
    descripcion: "Grupos de sociedades que consolidan su resultado fiscal.",
    aplica: ["MORAL"],
  },
  {
    clave: "610",
    nombre: "Residentes en el Extranjero",
    descripcion: "Sin establecimiento permanente en territorio nacional.",
    aplica: ["FISICA", "MORAL"],
  },
  {
    clave: "611",
    nombre: "Ingresos por Dividendos",
    descripcion: "Socios y accionistas que perciben utilidades distribuibles.",
    aplica: ["FISICA"],
  },
  {
    clave: "612",
    nombre: "Actividades Empresariales y Profesionales",
    descripcion: "Personas físicas con actividad empresarial o servicios profesionales.",
    aplica: ["FISICA"],
  },
  {
    clave: "614",
    nombre: "Ingresos por Intereses",
    descripcion: "Rendimientos financieros obtenidos por personas físicas.",
    aplica: ["FISICA"],
  },
  {
    clave: "615",
    nombre: "Obtención de Premios",
    descripcion: "Ingresos por premios, sorteos y concursos.",
    aplica: ["FISICA"],
  },
  {
    clave: "616",
    nombre: "Sin obligaciones fiscales",
    descripcion: "Personas físicas sin actividad económica registrada.",
    aplica: ["FISICA"],
  },
  {
    clave: "620",
    nombre: "Sociedades Cooperativas de Producción",
    descripcion: "Cooperativas que distribuyen ingresos entre sus socios.",
    aplica: ["MORAL"],
  },
  {
    clave: "621",
    nombre: "Incorporación Fiscal",
    descripcion: "Personas físicas con ingresos menores a 2 MDP.",
    aplica: ["FISICA"],
  },
  {
    clave: "622",
    nombre: "Actividades Agrícolas, Ganaderas y Silvícolas",
    descripcion: "Producción primaria y sus ingresos derivados.",
    aplica: ["FISICA", "MORAL"],
  },
  {
    clave: "623",
    nombre: "Opcional para Grupos de Sociedades",
    descripcion: "Sociedades integradas que determinan su resultado en grupo.",
    aplica: ["MORAL"],
  },
  {
    clave: "624",
    nombre: "Coordinados",
    descripcion: "Sociedades que coordinan actividades conjuntas.",
    aplica: ["MORAL"],
  },
  {
    clave: "625",
    nombre: "Plataformas Tecnológicas",
    descripcion: "Ingresos a través de plataformas digitales.",
    aplica: ["FISICA"],
  },
  {
    clave: "626",
    nombre: "Régimen Simplificado de Confianza (RESICO)",
    descripcion: "Personas físicas y morales con ingresos dentro del límite.",
    aplica: ["FISICA", "MORAL"],
  },
  {
    clave: "628",
    nombre: "Hidrocarburos",
    descripcion: "Personas morales con actividades de exploración y extracción.",
    aplica: ["MORAL"],
  },
  {
    clave: "629",
    nombre: "Regímenes Fiscales Preferentes",
    descripcion: "Empresas multinacionales con ingresos sujetos a REFIPRE.",
    aplica: ["MORAL"],
  },
  {
    clave: "630",
    nombre: "Enajenación de acciones en bolsa",
    descripcion: "Personas físicas que enajenan acciones en el mercado bursátil.",
    aplica: ["FISICA"],
  },
];

export const REGIMENES_POR_CLAVE = new Map(
  REGIMENES_SAT.map((regimen) => [regimen.clave, regimen]),
);

/** Botones principales del módulo, alineados a la paleta de la maqueta. */
export const BTN_PRIMARY =
  "inline-flex items-center justify-center gap-2 rounded-lg bg-gold-300 px-4 py-2.5 text-sm font-semibold text-navy-900 shadow-[0_6px_14px_rgb(245_213_71/35%)] transition hover:brightness-95 disabled:cursor-not-allowed disabled:opacity-60";
export const BTN_SECONDARY =
  "inline-flex items-center justify-center gap-2 rounded-lg border border-line bg-surface px-4 py-2.5 text-sm font-semibold text-ink transition hover:border-navy-900/20 hover:bg-app disabled:cursor-not-allowed disabled:opacity-60";
export const BTN_GHOST =
  "inline-flex items-center justify-center gap-2 rounded-lg px-4 py-2.5 text-sm font-semibold text-navy-800 transition hover:bg-navy-900/5 disabled:cursor-not-allowed disabled:opacity-60";
