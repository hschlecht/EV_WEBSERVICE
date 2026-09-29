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

from pydantic import BaseModel


def securiser_encodage_console() -> None:
    """Reconfigure stdout/stderr en UTF-8, en remplacant plutot qu'en
    plantant sur un caractere non representable par la console."""
    for flux in (sys.stdout, sys.stderr):
        try:
            flux.reconfigure(encoding="utf-8", errors="backslashreplace")
        except (AttributeError, ValueError):
            pass


def afficher_appel_entrant(logger: Logger, methode: str, chemin: str, client: str, corps_brut: bytes) -> None:
    """Journalise l'arrivee d'un appel HTTP sur le port d'ecoute et les
    donnees JSON brutes transmises, avant tout traitement (y compris avant
    la validation Pydantic) : utile pour diagnostiquer aussi les requetes
    malformees, qui n'atteindraient jamais afficher_requete()."""
    logger.info("Appel recu sur le port d'ecoute : %s %s depuis %s", methode, chemin, client)
    if not corps_brut:
        return
    texte_brut = corps_brut.decode("utf-8", errors="backslashreplace")
    logger.info("Donnees JSON brutes recues :\n%s", texte_brut)
    logger.info("Donnees JSON brutes recues (repr, tous caracteres) : %r", texte_brut)


def afficher_requete(logger: Logger, requete: BaseModel) -> None:
    """Journalise le detail des donnees POST JSON recues (avant la
    construction du titre/corps du message), en clair puis sous forme
    repr() pour garantir que chaque caractere est visible sans exception
    (y compris espaces, sauts de ligne, caracteres non imprimables ou non
    ASCII)."""
    json_compact = requete.model_dump_json()
    logger.info("Donnees POST JSON recues :\n%s", requete.model_dump_json(indent=2))
    logger.info("Donnees POST JSON recues (repr, tous caracteres) : %r", json_compact)


def afficher_message(logger: Logger, titre: str, corps: str) -> None:
    """Journalise le titre et le corps du message avant envoi, en clair
    puis sous forme repr() pour garantir que chaque caractere est visible
    sans exception (y compris espaces, sauts de ligne, caracteres non
    imprimables ou non ASCII)."""
    logger.info("Titre du message :\n%s", titre)
    logger.info("Titre du message (repr, tous caracteres) : %r", titre)
    logger.info("Corps du message (brut) avant envoi :\n%s", corps)
    logger.info("Corps du message (repr, tous caracteres) : %r", corps)
