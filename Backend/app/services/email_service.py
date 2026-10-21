from flask import current_app
from flask_mail import Message
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