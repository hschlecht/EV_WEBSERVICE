"""Envoi de mail en texte brut via SMTP (bibliotheque standard uniquement).

Ne depend plus d'Outlook : le message part directement par SMTP
(Office 365 / Exchange Online par defaut), ce qui evite les
reformatages/fusions de lignes lies au client de messagerie.
"""

from __future__ import annotations

import os
import smtplib
from email.message import EmailMessage

SMTP_HOST = os.environ.get("SMTP_HOST", "smtp.office365.com")
SMTP_PORT = int(os.environ.get("SMTP_PORT", "587"))
SMTP_USER = os.environ.get("SMTP_USER")
SMTP_PASSWORD = os.environ.get("SMTP_PASSWORD")
SMTP_FROM = os.environ.get("SMTP_FROM", SMTP_USER)


class MailError(RuntimeError):
    """Erreur remontee lorsque l'envoi du mail echoue."""


def send_mail(destinataire: str, titre: str, corps: str = "") -> None:
    """Envoie un email en texte brut via SMTP (STARTTLS)."""
    if not SMTP_USER or not SMTP_PASSWORD:
        raise MailError(
            "Configuration SMTP manquante : definir les variables "
            "d'environnement SMTP_USER et SMTP_PASSWORD."
        )

    message = EmailMessage()
    message["From"] = SMTP_FROM
    message["To"] = destinataire
    message["Subject"] = titre
    message.set_content(corps)  # Content-Type: text/plain par defaut

    try:
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=30) as smtp:
            smtp.starttls()
            smtp.login(SMTP_USER, SMTP_PASSWORD)
            smtp.send_message(message)
    except (smtplib.SMTPException, OSError) as exc:
        raise MailError(f"Echec de l'envoi du mail via SMTP: {exc}") from exc
