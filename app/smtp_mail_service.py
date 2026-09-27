"""Envoi de mail en texte brut via SMTP (bibliotheque standard uniquement).

Construction du message alignee sur un script maison fonctionnel (envoi
direct vers un relai anonyme Exchange Online Protection, sans TLS ni
authentification) : le message est un texte brut minimal
"Subject: ...\\r\\n\\r\\n<corps>\\r\\n", envoye tel quel via
smtplib.sendmail(). On evite volontairement email.message.EmailMessage :
son encodage MIME automatique (quoted-printable des que le corps contient
un caractere non-ASCII, ou simplement des lignes longues) echappe les
caracteres "=" du corps (Centre_de_services=..., Service=..., etc.) en
"=3D", ce qu'un parser ITSM lisant le texte brut sans decodage MIME ne
sait pas reinterpreter.

Pense a l'endpoint EOP specifique au tenant, du type
"<tenant>.mail.protection.outlook.com" (port 25, sans TLS ni
authentification), plutot que smtp.office365.com (qui exige TLS +
authentification et peut rejeter un relai anonyme avec une erreur
"wrong Office 365 region").

La configuration peut venir de variables d'environnement classiques et/ou
d'un fichier config.env a la racine du projet (voir app/config.py et
config.env.example) : une variable d'environnement deja definie reste
prioritaire sur le fichier.
"""

from __future__ import annotations

import os
import smtplib

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

    Message construit "a la main" (pas de MIME/email.message), pour
    eviter tout encodage (quoted-printable, etc.) qui alterait le corps
    en texte brut. Sans authentification par defaut (relai anonyme) ; si
    SMTP_USER et SMTP_PASSWORD sont definis, une authentification est
    effectuee (avec STARTTLS prealable si SMTP_USE_TLS est active).
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

    message = f"Subject: {titre}\r\n\r\n{corps}\r\n"

    try:
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=30) as smtp:
            smtp.ehlo()
            if SMTP_USE_TLS:
                smtp.starttls()
            if SMTP_USER and SMTP_PASSWORD:
                smtp.login(SMTP_USER, SMTP_PASSWORD)
            # Encode nous-memes en UTF-8 : envoyer un str obligerait
            # smtplib a l'encoder en ASCII strict et a planter au premier
            # caractere accentue.
            smtp.sendmail(SMTP_FROM, destinataire, message.encode("utf-8"))
    except (smtplib.SMTPException, OSError) as exc:
        raise MailError(f"Echec de l'envoi du mail via SMTP: {exc}") from exc
