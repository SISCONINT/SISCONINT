/** Los 31 estados + CDMX, en el orden oficial del catálogo INEGI. */
export const ESTADOS_MEXICO = [
  "Aguascalientes",
  "Baja California",
  "Baja California Sur",
  "Campeche",
  "Chiapas",
  "Chihuahua",
  "Ciudad de México",
  "Coahuila",
  "Colima",
  "Durango",
  "Guanajuato",
  "Guerrero",
  "Hidalgo",
  "Jalisco",
  "México",
  "Michoacán",
  "Morelos",
  "Nayarit",
  "Nuevo León",
  "Oaxaca",
  "Puebla",
  "Querétaro",
  "Quintana Roo",
  "San Luis Potosí",
  "Sinaloa",
  "Sonora",
  "Tabasco",
  "Tamaulipas",
  "Tlaxcala",
  "Veracruz",
  "Yucatán",
  "Zacatecas",
] as const;

export type EstadoMexico = (typeof ESTADOS_MEXICO)[number];

const NORMALIZADOS = new Map(ESTADOS_MEXICO.map((e) => [normalizar(e), e]));

function normalizar(value: string): string {
  return value
    .trim()
    .toLowerCase()
    .normalize("NFD")
    .replace(/[̀-ͯ]/g, ""); // quita acentos para comparar sin importar cómo los tecleen
}

/** Valida y devuelve el nombre oficial (con su acentuación correcta) o null si no es un estado válido. */
export function resolverEstado(value: string): EstadoMexico | null {
  return (NORMALIZADOS.get(normalizar(value)) as EstadoMexico | undefined) ?? null;
}

export function esEstadoValido(value: string): boolean {
  return resolverEstado(value) !== null;
}
