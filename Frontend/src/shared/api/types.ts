export interface ApiResponse<T>{
    data: T;
    meta?: {page: number; per_page: number; total: number; pages?: number}
}

export interface ApiErrorBody{
    error: {
        code: string;
        message: string;
        fields?: Record<string, string[]>;
        retry_after: number;
    };
}

export class ApiError extends Error {
  status: number;
  code: string;
  fields?: Record<string, string[]>;
  retryAfter?: number;

  constructor(
    status: number,
    code: string,
    message: string,
    fields?: Record<string, string[]>,
    retryAfter?: number,
  ) {
    super(message);
    this.status = status;
    this.code = code;
    this.fields = fields;
    this.retryAfter = retryAfter;
  }
}

export interface PageMeta {
  page: number;
  per_page: number;
  total: number;
}

export interface Paginated<T> {
  data: T[];
  meta: PageMeta;
}