export interface PlantillaCorreo {
  id: number;
  clave: string;
  nombre: string;
  asunto: string;
  cuerpo: string;
  activa: boolean;
}

export interface PlantillaFormValues {
  clave: string;
  nombre: string;
  asunto: string;
  cuerpo: string;
  activa: boolean;
}
