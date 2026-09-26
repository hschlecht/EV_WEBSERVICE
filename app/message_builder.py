"""Construction du titre et du corps du mail (partagee entre les
webservices Outlook et SMTP)."""

from __future__ import annotations

import re
from datetime import datetime

from pydantic import BaseModel, EmailStr, Field

SEPARATEUR_LIGNES = re.compile(r"\r\n|\r|\n")


class MailRequest(BaseModel):
    adresse_mail: EmailStr = Field(..., description="Adresse mail du destinataire")
    var_cds: str = Field(..., min_length=1, description="Centre de services")
    var_service: str = Field(..., min_length=1, description="Service")
    var_demandeur: str = Field(..., min_length=1, description="Demandeur")
    var_client: str = Field(..., min_length=1, description="Client (utilise aussi dans le titre)")
    var_adresse: str = Field(..., min_length=1, description="Adresse du site")
    var_libelle: str = Field(..., min_length=1, description="Libelle")
    var_symptome: str = Field(
        ..., min_length=1, description="Contenu de Symptome (peut contenir plusieurs lignes, separees par \\n)"
    )


class MailResponse(BaseModel):
    statut: str
    message: str


def construire_titre(var_client: str) -> str:
    horodatage = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    return f"CASE OPENNING - {var_client} - {horodatage}"


CORPS_LIGNES = [
    "Centre_de_services={var_cds}",
    "Service={var_service}",
    "Demandeur={var_demandeur}",
    "Client={var_client}",
    "Adresse_site={var_adresse}",
    "Equipe=EQ-0154",
    "Intervenant=",
    "ORIGINE=EMAIL",
    "Dossier_interne=06ad802324a87214306c3b04d9acf7747fdf86af",
    "impact=1 - Faible / Low",
    "urgence=1 - Faible / Low",
    "Libelle={var_libelle}",
]


def construire_bloc_symptome(var_symptome: str) -> list[str]:
    # Certains clients (formulaire, Swagger...) envoient la sequence
    # litterale antislash+n plutot qu'un vrai caractere de retour a la
    # ligne : on la normalise avant de decouper.
    normalise = var_symptome.replace("\\r\\n", "\n").replace("\\n", "\n").replace("\\r", "\n")
    premiere, *suite = SEPARATEUR_LIGNES.split(normalise)
    return [f"Symptome={premiere}", *suite]


def construire_corps_lignes(
    var_cds: str,
    var_service: str,
    var_demandeur: str,
    var_client: str,
    var_adresse: str,
    var_libelle: str,
    var_symptome: str,
) -> list[str]:
    lignes = [
        ligne.format(
            var_cds=var_cds,
            var_service=var_service,
            var_demandeur=var_demandeur,
            var_client=var_client,
            var_adresse=var_adresse,
            var_libelle=var_libelle,
        )
        for ligne in CORPS_LIGNES
    ]
    lignes.extend(construire_bloc_symptome(var_symptome))
    return ["", *lignes]
