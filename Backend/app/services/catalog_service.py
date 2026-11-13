"""HU_25-28. Lógica de negocio del catálogo de proyectos y actividades."""
from app.core import audit
from app.core.datetime_utils import utcnow
from app.core.errors import NotFoundError, ValidationAppError
from app.extensions import db
from app.models.catalog import CategoriaProyecto
from app.repositories import catalog_repository

MSG_NOMBRE_DUPLICADO = "Ya existe una entrada con ese nombre en este nivel del catálogo"
MSG_SOLO_DOS_NIVELES = "El catálogo solo admite categorías y subcategorías"
MSG_NO_ENCONTRADA = "La entrada del catálogo no existe"


def list_categorias(q: str | None, solo_activas: bool) -> list[dict]:
    """Devuelve el árbol de categorías listo para serializar (categoría -> subcategorías)."""
    raices: list[CategoriaProyecto] = catalog_repository.list_categorias(q, solo_activas)
    return [c.to_dict(incluir_subcategorias=True) for c in raices]


def create_categoria(actor, data: dict) -> dict:
    """HU_26: crea una categoría raíz o una subcategoría (máximo dos niveles)."""
    padre_id = data.get("padre_id")
    if padre_id is not None:
        padre = catalog_repository.get_by_id(padre_id)
        if padre is None:
            raise NotFoundError("La categoría padre no existe", fields={"padre_id": ["No existe"]})
        if padre.padre_id is not None:
            raise ValidationAppError(
                MSG_SOLO_DOS_NIVELES, fields={"padre_id": [MSG_SOLO_DOS_NIVELES]}
            )

    if catalog_repository.nombre_existe(data["nombre"], padre_id):
        raise ValidationAppError(
            MSG_NOMBRE_DUPLICADO, fields={"nombre": [MSG_NOMBRE_DUPLICADO]}
        )

    categoria = CategoriaProyecto(
        padre_id=padre_id,
        nombre=data["nombre"],
        orden=data.get("orden", 0),
        activa=data.get("activa", True),
    )
    catalog_repository.add(categoria)
    audit.log(
        actor.id,
        "categoria_proyecto",
        categoria.id,
        audit.CREAR,
        {"nombre": categoria.nombre, "padre_id": categoria.padre_id},
    )
    db.session.commit()
    return categoria.to_dict(incluir_subcategorias=categoria.padre_id is None)


def update_categoria(actor, categoria_id: int, data: dict) -> dict:
    """HU_27: edita nombre, orden o estatus de una entrada del catálogo."""
    categoria = _get(categoria_id)

    nombre = data.get("nombre", categoria.nombre)
    if nombre != categoria.nombre and catalog_repository.nombre_existe(
        nombre, categoria.padre_id, exclude_id=categoria.id
    ):
        raise ValidationAppError(
            MSG_NOMBRE_DUPLICADO, fields={"nombre": [MSG_NOMBRE_DUPLICADO]}
        )

    antes = {"nombre": categoria.nombre, "orden": categoria.orden, "activa": categoria.activa}
    categoria.nombre = nombre
    categoria.orden = data.get("orden", categoria.orden)
    if "activa" in data:
        categoria.activa = data["activa"]

    subcategorias_desactivadas = 0
    if categoria.padre_id is None and antes["activa"] and not categoria.activa:
        # HU_28: al desactivar una categoría también se desactivan sus subcategorías.
        subcategorias_desactivadas = catalog_repository.deactivate_children(
            categoria.id, utcnow()
        )

    audit.log(
        actor.id,
        "categoria_proyecto",
        categoria.id,
        audit.MODIFICAR,
        {
            campo: {"antes": antes[campo], "despues": getattr(categoria, campo)}
            for campo in antes
            if antes[campo] != getattr(categoria, campo)
        },
    )
    db.session.commit()
    resultado = categoria.to_dict(incluir_subcategorias=categoria.padre_id is None)
    resultado["subcategorias_desactivadas"] = subcategorias_desactivadas
    return resultado


def deactivate_categoria(actor, categoria_id: int) -> dict:
    """HU_28: desactiva una entrada y, si es raíz, sus subcategorías."""
    categoria = _get(categoria_id)
    categoria.activa = False
    subcategorias_desactivadas = 0
    if categoria.padre_id is None:
        subcategorias_desactivadas = catalog_repository.deactivate_children(
            categoria.id, utcnow()
        )

    audit.log(
        actor.id,
        "categoria_proyecto",
        categoria.id,
        audit.ESTATUS,
        {"activa": False, "subcategorias_desactivadas": subcategorias_desactivadas},
    )
    db.session.commit()
    resultado = categoria.to_dict(incluir_subcategorias=categoria.padre_id is None)
    resultado["subcategorias_desactivadas"] = subcategorias_desactivadas
    return resultado


def _get(categoria_id: int) -> CategoriaProyecto:
    categoria = catalog_repository.get_by_id(categoria_id)
    if categoria is None:
        raise NotFoundError(MSG_NO_ENCONTRADA)
    return categoria
