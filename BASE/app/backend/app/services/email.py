"""Entrega de correo SMTP configurada por variables de entorno."""
from __future__ import annotations

import smtplib
from email.message import EmailMessage

from ..config import settings


class EmailDeliveryError(RuntimeError):
    pass


def smtp_configurado() -> bool:
    return bool(settings.smtp_host and settings.email_from)


def enviar_email(destino: str, asunto: str, cuerpo: str) -> None:
    if not smtp_configurado():
        raise EmailDeliveryError("SMTP no configurado")

    mensaje = EmailMessage()
    mensaje["From"] = settings.email_from
    mensaje["To"] = destino
    mensaje["Subject"] = asunto
    mensaje.set_content(cuerpo)

    try:
        with smtplib.SMTP(settings.smtp_host, settings.smtp_port,
                          timeout=10) as smtp:
            smtp.ehlo()
            if smtp_user_configurado():
                smtp.starttls()
                smtp.login(settings.smtp_user, settings.smtp_password)
            smtp.send_message(mensaje)
    except (smtplib.SMTPException, OSError) as exc:
        raise EmailDeliveryError("No se pudo entregar el correo") from exc


def smtp_user_configurado() -> bool:
    return bool(settings.smtp_user and settings.smtp_password)
