"""RG-07: listados de 20 registros por página, con paginación y total de resultados."""
from flask_sqlalchemy.pagination import Pagination

PER_PAGE = 20  # fijo: el cliente no puede cambiarlo


def pagination_meta(page: Pagination) -> dict:
    return {"page": page.page, "per_page": page.per_page, "total": page.total, "pages": page.pages}