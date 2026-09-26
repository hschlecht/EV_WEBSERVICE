"""Chargement optionnel d'un fichier de configuration (KEY=VALUE) dans les
variables d'environnement. Bibliotheque standard uniquement.

Une variable d'environnement deja definie (avant le lancement du
webservice) est toujours prioritaire sur le fichier.
"""

from __future__ import annotations

import os
from pathlib import Path

RACINE_PROJET = Path(__file__).resolve().parent.parent
FICHIER_CONFIG_DEFAUT = RACINE_PROJET / "config.env"


def charger_fichier_config(chemin: str | Path = FICHIER_CONFIG_DEFAUT) -> None:
    """Lit un fichier texte simple (une variable par ligne, `CLE=valeur`,
    lignes vides et commentaires `#` ignores) et alimente os.environ pour
    chaque cle pas deja definie."""
    chemin_config = Path(chemin)
    if not chemin_config.is_file():
        return

    for ligne in chemin_config.read_text(encoding="utf-8").splitlines():
        ligne = ligne.strip()
        if not ligne or ligne.startswith("#"):
            continue
        cle, separateur, valeur = ligne.partition("=")
        if not separateur:
            continue
        os.environ.setdefault(cle.strip(), valeur.strip())
