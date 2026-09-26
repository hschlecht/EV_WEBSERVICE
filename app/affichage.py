"""Utilitaires d'affichage console robustes.

Sur certaines consoles Windows (cp1252, cp850...), l'encodage par defaut
ne supporte pas tous les caracteres (accents, tiret demi-cadratin '-',
etc.) : cela peut soit faire planter l'affichage, soit faire disparaitre
silencieusement des caracteres. Ce module force un encodage UTF-8 robuste
et journalise en plus une forme repr() qui rend visible, sans exception,
absolument tous les caracteres (espaces, sauts de ligne, caracteres
invisibles inclus).
"""

from __future__ import annotations

import sys
from logging import Logger


def securiser_encodage_console() -> None:
    """Reconfigure stdout/stderr en UTF-8, en remplacant plutot qu'en
    plantant sur un caractere non representable par la console."""
    for flux in (sys.stdout, sys.stderr):
        try:
            flux.reconfigure(encoding="utf-8", errors="backslashreplace")
        except (AttributeError, ValueError):
            pass


def afficher_message(logger: Logger, titre: str, corps: str) -> None:
    """Journalise le titre et le corps du message avant envoi, en clair
    puis sous forme repr() pour garantir que chaque caractere est visible
    sans exception (y compris espaces, sauts de ligne, caracteres non
    imprimables ou non ASCII)."""
    logger.info("Titre du message :\n%s", titre)
    logger.info("Titre du message (repr, tous caracteres) : %r", titre)
    logger.info("Corps du message (brut) avant envoi :\n%s", corps)
    logger.info("Corps du message (repr, tous caracteres) : %r", corps)
