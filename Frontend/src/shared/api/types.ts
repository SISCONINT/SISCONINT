export interface ApiResponse<T>{
    data: T;
    meta?: {page: number; per_page: number, total: number, pages?: number}
}

export interface ApiErrorBody{
    error: {
        code: string;
        message: string;
        fields?: Record<string, string[]>;
        retry_after: number;
        [key: string]: unknown;
    };
}

export class ApiError extends Error {
  status: number;
  code: string;
  fields?: Record<string, string[]>;
  retryAfter?: number;
  /** Resto de claves que el backend añade al error (p. ej. subtareas_pendientes en 409). */
  extra?: Record<string, unknown>;

  constructor(
    status: number,
    code: string,
    message: string,
    fields?: Record<string, string[]>,
    retryAfter?: number,
    extra?: Record<string, unknown>,
  ) {
    super(message);
    this.status = status;
    this.code = code;
    this.fields = fields;
    this.retryAfter = retryAfter;
    this.extra = extra;
  }
}