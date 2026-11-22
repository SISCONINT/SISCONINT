"""Minutas y acuerdos: validación y almacenamiento de archivos."""
from pathlib import Path
from uuid import uuid4

from flask import current_app, send_file
from werkzeug.utils import secure_filename

from app.core import audit
from app.core.datetime_utils import utcnow
from app.core.errors import ForbiddenError, NotFoundError, ValidationAppError
from app.core.permissions import ROL_ADMINISTRADOR, ROL_COORDINADOR, ROL_DUENO
from app.extensions import db
from app.models.client import Cliente
from app.models.minute import (
    MAX_BYTES,
    MIMES_PERMITIDOS,
    TIPO_CLIENTE,
    TIPO_PERSONAL,
    TIPOS,
    Minuta,
)
from app.models.task import Tarea
from app.repositories import minute_repository

EXTENSION_MIME = {
    ".pdf": "application/pdf",
    ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    ".xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".png": "image/png",
}

MSG_ARCHIVO_REQUERIDO = "Adjunta el archivo de la minuta"
MSG_ARCHIVO_MIME = "El archivo debe ser PDF, DOCX, XLSX, JPG o PNG"
MSG_ARCHIVO_TAMANO = "El archivo debe pesar entre 1 byte y 10 MB"


def list_minutes(filtros: dict):
    return minute_repository.search(
        cliente_id=filtros.get("cliente"), tarea_id=filtros.get("tarea"), page=filtros["page"]
    )


def _validar(data: dict) -> None:
    tipo = data.get("tipo")
    if tipo not in TIPOS:
        raise ValidationAppError("Tipo de minuta no válido", fields={"tipo": ["Valor no válido"]})

    if tipo == TIPO_CLIENTE and data.get("cliente_id") is None:
        raise ValidationAppError(
            "Selecciona el cliente de la minuta",
            fields={"cliente_id": ["Campo obligatorio para minutas de cliente"]},
        )
    if tipo == TIPO_PERSONAL and data.get("cliente_id") is not None:
        raise ValidationAppError(
            "Las minutas personales no llevan cliente",
            fields={"cliente_id": ["Debe quedar vacío para minutas personales"]},
        )

    if data.get("cliente_id") is not None:
        cliente = db.session.get(Cliente, data["cliente_id"])
        if cliente is None or cliente.deleted_at is not None:
            raise ValidationAppError(
                "El cliente no es válido", fields={"cliente_id": ["Cliente no encontrado"]}
            )

    if data.get("tarea_id") is not None:
        if data.get("cliente_id") is None:
            raise ValidationAppError(
                "La tarea requiere un cliente",
                fields={"tarea_id": ["Selecciona primero el cliente"]},
            )
        tarea = db.session.get(Tarea, data["tarea_id"])
        if tarea is None or tarea.deleted_at is not None:
            raise ValidationAppError(
                "La tarea no es válida", fields={"tarea_id": ["Tarea no encontrada"]}
            )
        if tarea.cliente_id != data["cliente_id"]:
            raise ValidationAppError(
                "La tarea no pertenece al cliente seleccionado",
                fields={"tarea_id": ["La tarea pertenece a otro cliente"]},
            )


def _mime_permitido(archivo) -> str:
    mime = (archivo.mimetype or "").lower()
    if mime in MIMES_PERMITIDOS:
        return mime
    extension = Path(secure_filename(archivo.filename or "")).suffix.lower()
    return EXTENSION_MIME.get(extension, "")


def _guardar_archivo(archivo) -> tuple[str, str, str, int]:
    """Valida y guarda el archivo. Devuelve (nombre original, ruta, mime, bytes)."""
    if archivo is None or not archivo.filename:
        raise ValidationAppError(
            MSG_ARCHIVO_REQUERIDO, fields={"archivo": [MSG_ARCHIVO_REQUERIDO]}
        )

    mime = _mime_permitido(archivo)
    if not mime:
        raise ValidationAppError(MSG_ARCHIVO_MIME, fields={"archivo": [MSG_ARCHIVO_MIME]})

    contenido = archivo.read()
    tamano = len(contenido)
    if tamano < 1 or tamano > MAX_BYTES:
        raise ValidationAppError(MSG_ARCHIVO_TAMANO, fields={"archivo": [MSG_ARCHIVO_TAMANO]})

    nombre_original = secure_filename(archivo.filename) or "archivo"
    nombre_guardado = f"{uuid4().hex}_{nombre_original}"
    carpeta = Path(current_app.config["UPLOAD_FOLDER"]) / "minutas"
    carpeta.mkdir(parents=True, exist_ok=True)
    (carpeta / nombre_guardado).write_bytes(contenido)

    return nombre_original, nombre_guardado, mime, tamano


def _borrar_archivo(ruta: str | None) -> None:
    if not ruta:
        return
    try:
        (Path(current_app.config["UPLOAD_FOLDER"]) / "minutas" / ruta).unlink(missing_ok=True)
    except OSError:
        current_app.logger.warning("No se pudo eliminar la minuta %s", ruta)


def create_minute(actor, data: dict, archivo) -> Minuta:
    _validar(data)
    nombre, ruta, mime, tamano = _guardar_archivo(archivo)

    minuta = Minuta(
        tipo=data["tipo"],
        titulo=data["titulo"],
        fecha_reunion=data["fecha_reunion"],
        cliente_id=data.get("cliente_id"),
        tarea_id=data.get("tarea_id"),
        observaciones=data.get("observaciones"),
        cargada_por=actor.id,
        archivo_nombre=nombre,
        archivo_ruta=ruta,
        archivo_mime=mime,
        archivo_bytes=tamano,
        created_by=actor.id,
        updated_by=actor.id,
    )
    db.session.add(minuta)
    db.session.flush()
    audit.log(actor.id, "minuta", minuta.id, audit.CREAR, {"titulo": minuta.titulo})
    db.session.commit()
    return minuta


def get_minute(minuta_id: int) -> Minuta:
    minuta = minute_repository.get_by_id(minuta_id)
    if minuta is None:
        raise NotFoundError("Minuta no encontrada")
    return minuta


def _assert_can_edit(actor, minuta: Minuta) -> None:
    if actor.rol in (ROL_DUENO, ROL_ADMINISTRADOR, ROL_COORDINADOR):
        return
    if minuta.cargada_por == actor.id:
        return
    raise ForbiddenError()


def update_minute(actor, minuta_id: int, data: dict, archivo=None) -> Minuta:
    minuta = get_minute(minuta_id)
    _assert_can_edit(actor, minuta)
    _validar(data)

    ruta_anterior = None
    if archivo is not None and archivo.filename:
        nombre, ruta, mime, tamano = _guardar_archivo(archivo)
        ruta_anterior = minuta.archivo_ruta
        minuta.archivo_nombre = nombre
        minuta.archivo_ruta = ruta
        minuta.archivo_mime = mime
        minuta.archivo_bytes = tamano

    minuta.tipo = data["tipo"]
    minuta.titulo = data["titulo"]
    minuta.fecha_reunion = data["fecha_reunion"]
    minuta.cliente_id = data.get("cliente_id")
    minuta.tarea_id = data.get("tarea_id")
    minuta.observaciones = data.get("observaciones")
    minuta.updated_by = actor.id
    audit.log(actor.id, "minuta", minuta.id, audit.MODIFICAR, {"titulo": minuta.titulo})
    db.session.commit()

    if ruta_anterior:
        _borrar_archivo(ruta_anterior)
    return minuta


def delete_minute(actor, minuta_id: int) -> None:
    minuta = get_minute(minuta_id)
    _assert_can_edit(actor, minuta)
    minuta.deleted_at = utcnow()
    minuta.updated_by = actor.id
    audit.log(actor.id, "minuta", minuta.id, audit.ELIMINAR, {"titulo": minuta.titulo})
    db.session.commit()


def download_minute(minuta_id: int):
    minuta = get_minute(minuta_id)
    ruta = Path(current_app.config["UPLOAD_FOLDER"]) / "minutas" / minuta.archivo_ruta
    if not ruta.is_file():
        raise NotFoundError("El archivo de la minuta no está disponible")
    return send_file(
        ruta,
        mimetype=minuta.archivo_mime,
        download_name=minuta.archivo_nombre,
        as_attachment=False,
    )
