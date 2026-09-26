"""Envoi de mail en texte brut via SMTP (bibliotheque standard uniquement).

Ne depend pas d'Outlook : le message part directement par SMTP. Pense a un
relai SMTP interne sans authentification par defaut (port 25, pas de
TLS) ; l'authentification et le TLS restent disponibles si le serveur en
a besoin.

La configuration peut venir de variables d'environnement classiques et/ou
d'un fichier config.env a la racine du projet (voir app/config.py et
config.env.example) : une variable d'environnement deja definie reste
prioritaire sur le fichier.
"""

from __future__ import annotations

import os
import smtplib
from email.message import EmailMessage

from app.config import charger_fichier_config

charger_fichier_config()


def _lire_booleen(nom: str, defaut: bool) -> bool:
    valeur = os.environ.get(nom)
    if valeur is None:
        return defaut
    return valeur.strip().lower() in {"1", "true", "vrai", "oui", "yes"}


SMTP_HOST = os.environ.get("SMTP_HOST")
SMTP_PORT = int(os.environ.get("SMTP_PORT", "25"))
SMTP_USE_TLS = _lire_booleen("SMTP_USE_TLS", defaut=False)
SMTP_USER = os.environ.get("SMTP_USER")
SMTP_PASSWORD = os.environ.get("SMTP_PASSWORD")
SMTP_FROM = os.environ.get("SMTP_FROM", SMTP_USER)


class MailError(RuntimeError):
    """Erreur remontee lorsque l'envoi du mail echoue."""


def send_mail(destinataire: str, titre: str, corps: str = "") -> None:
    """Envoie un email en texte brut via SMTP.

    Sans authentification par defaut (relai SMTP interne). Si SMTP_USER et
    SMTP_PASSWORD sont definis, une authentification est effectuee (avec
    STARTTLS prealable si SMTP_USE_TLS est active).
    """
    if not SMTP_HOST:
        raise MailError(
            "Configuration SMTP manquante : definir la variable "
            "d'environnement SMTP_HOST (adresse du serveur/relai SMTP)."
        )
    if not SMTP_FROM:
        raise MailError(
            "Configuration SMTP manquante : definir SMTP_FROM (ou SMTP_USER) "
            "pour l'adresse d'expedition."
        )

    message = EmailMessage()
    message["From"] = SMTP_FROM
    message["To"] = destinataire
    message["Subject"] = titre
    message.set_content(corps)  # Content-Type: text/plain par defaut

    try:
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=30) as smtp:
            if SMTP_USE_TLS:
                smtp.starttls()
            if SMTP_USER and SMTP_PASSWORD:
                smtp.login(SMTP_USER, SMTP_PASSWORD)
            smtp.send_message(message)
    except (smtplib.SMTPException, OSError) as exc:
        raise MailError(f"Echec de l'envoi du mail via SMTP: {exc}") from exc
