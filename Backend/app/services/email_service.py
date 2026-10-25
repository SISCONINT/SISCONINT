from flask import current_app
from flask_mail import Message
from app.core.datetime_utils import TZ_MX, as_utc
from app.extensions import mail

def send_activation_email(user, raw_token: str) -> bool:
    """Envía el correo con el enlace de activación. Retorna True si se envió."""
    activation_url = f"{current_app.config['FRONTEND_URL']}/activar?token={raw_token}"

    # Si estamos en desarrollo y no hay MAIL_SERVER, imprimimos en consola
    if not current_app.config.get("MAIL_SERVER"):
        current_app.logger.info("=== ENLACE DE ACTIVACIÓN (desarrollo) ===")
        current_app.logger.info(activation_url)
        return False  # O True, según cómo quieras reportarlo en HU_05

    msg = Message(
        subject="Activa tu cuenta en SISCONNIT",
        recipients=[user.correo_institucional],
    )
    msg.body = f"""Hola {user.nombre_completo},

Para definir tu contraseña y acceder al sistema, abre el siguiente enlace (válido por 48 horas):

{activation_url}

Si no solicitaste esto, ignora este correo.

Atentamente,
Téllez Ponce y Asociados
"""
    try:
        mail.send(msg)
        return True
    except Exception as e:
        current_app.logger.error(f"Error enviando correo a {user.correo_institucional}: {e}")
        return False


def send_task_completed_email(cliente, tarea, destinatario: str) -> bool:
    """HU_70: avisa al cliente (sin acceso al sistema) que su trámite concluyó.

    La tarea ya está en Completado. Sin MAIL_SERVER (desarrollo) solo deja el aviso
    en el log y devuelve False, para no marcar `cliente_notificado` sin haber
    enviado nada. Retorna True si el correo salió.
    """
    if not current_app.config.get("MAIL_SERVER"):
        current_app.logger.info("=== TRÁMITE CONCLUIDO (desarrollo) ===")
        current_app.logger.info(
            "%s: %s (%s)", cliente.nombre_completo, tarea.titulo, tarea.completada_en
        )
        return False

    fecha_conclusion = as_utc(tarea.completada_en).astimezone(TZ_MX).strftime("%d/%m/%Y")
    msg = Message(
        subject=f"Conclusión de trámite: {tarea.titulo}",
        recipients=[destinatario],
    )
    msg.body = f"""Hola {cliente.nombre_completo},

Le informamos que el trámite «{tarea.titulo}» concluyó el {fecha_conclusion}.

Atentamente,
Téllez Ponce y Asociados
"""
    try:
        mail.send(msg)
        return True
    except Exception as e:
        current_app.logger.error(f"Error enviando correo a {destinatario}: {e}")
        return False
