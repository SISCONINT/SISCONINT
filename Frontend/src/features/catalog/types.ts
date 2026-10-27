export interface Subcategoria {
  id: number;
  nombre: string;
  activa: boolean;
  orden: number;
}

export interface Categoria extends Subcategoria {
  subcategorias: Subcategoria[];
}

export interface CatalogFilters {
  q?: string;
  solo_activas?: boolean;
}
