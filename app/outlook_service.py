"""Pilotage d'Outlook Desktop via COM (pywin32).

Ce module ne fonctionne que sous Windows, avec Outlook installe localement.
"""

from __future__ import annotations

import logging
import time

import psutil
import pythoncom
import win32com.client
from pywintypes import com_error

logger = logging.getLogger("outlook_service")

OUTLOOK_PROCESS_NAME = "OUTLOOK.EXE"
OL_MAIL_ITEM = 0  # olMailItem


class OutlookError(RuntimeError):
    """Erreur remontee lorsque Outlook ne peut pas etre demarre ou pilote."""


def _is_outlook_running() -> bool:
    for proc in psutil.process_iter(["name"]):
        try:
            if (proc.info["name"] or "").lower() == OUTLOOK_PROCESS_NAME.lower():
                return True
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    return False


def _connect_with_retry(timeout_seconds: int = 30, interval_seconds: float = 1.0):
    """Se connecte a l'instance Outlook.Application, en reessayant pendant
    le demarrage de l'application (RPC pas encore disponible)."""
    deadline = time.time() + timeout_seconds
    last_error: Exception | None = None

    while time.time() < deadline:
        try:
            # Dispatch demarre Outlook si aucune instance COM n'est enregistree.
            application = win32com.client.Dispatch("Outlook.Application")
            # Force un appel reel pour verifier que l'instance repond deja.
            _ = application.Session
            return application
        except com_error as exc:
            last_error = exc
            time.sleep(interval_seconds)

    raise OutlookError(
        f"Impossible de se connecter a Outlook apres {timeout_seconds}s: {last_error}"
    )


def ensure_outlook_running(timeout_seconds: int = 30):
    """Verifie si Outlook est deja charge ; sinon le lance, puis retourne
    l'objet COM Outlook.Application pret a l'emploi."""
    pythoncom.CoInitialize()
    try:
        if _is_outlook_running():
            logger.info("Outlook est deja en cours d'execution.")
        else:
            logger.info("Outlook n'est pas demarre, lancement en cours...")
        return _connect_with_retry(timeout_seconds=timeout_seconds)
    finally:
        pythoncom.CoUninitialize()


def send_mail(destinataire: str, titre: str, corps: str = "", timeout_seconds: int = 30) -> None:
    """Envoie un email via Outlook Desktop, en demarrant Outlook si necessaire."""
    pythoncom.CoInitialize()
    try:
        application = ensure_outlook_running(timeout_seconds=timeout_seconds)
        mail = application.CreateItem(OL_MAIL_ITEM)
        mail.To = destinataire
        mail.Subject = titre
        mail.Body = corps
        mail.Send()
        logger.info("Mail envoye a %s avec le titre '%s'.", destinataire, titre)
    except com_error as exc:
        raise OutlookError(f"Echec de l'envoi du mail via Outlook: {exc}") from exc
    finally:
        pythoncom.CoUninitialize()
