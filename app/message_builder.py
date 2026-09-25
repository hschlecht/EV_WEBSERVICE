"""Construction du titre et du corps du mail (partagee entre les
webservices Outlook et SMTP)."""

from __future__ import annotations

import re
from datetime import datetime

from pydantic import BaseModel, EmailStr, Field

SEPARATEUR_LIGNES = re.compile(r"\r\n|\r|\n")


class MailRequest(BaseModel):
    adresse_mail: EmailStr = Field(..., description="Adresse mail du destinataire")
    client: str = Field(..., min_length=1, description="Nom du client (VAR_1 du titre et du corps)")
    ev_id: str = Field(..., min_length=1, description="Identifiant EvObserve (remplace ID dans Libelle)")
    sympt_var: str = Field(
        ..., min_length=1, description="Contenu de Symptome (peut contenir plusieurs lignes, separees par \\n)"
    )


class MailResponse(BaseModel):
    statut: str
    message: str


def construire_titre(client: str) -> str:
    horodatage = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    return f"CASE OPENNING - {client} - {horodatage}"


CORPS_LIGNES = [
    "Centre_de_services=CDS-008",
    "Service= CDSCAEN0017",
    "Demandeur=28508",
    "Client= {client}",
    "Adresse_site= {client}",
    "Equipe=EQ-0154",
    "Intervenant=",
    "ORIGINE=EVENEMENT",
    "Dossier_interne=Supervision EvObserve - {client}",
    "impact= 2 - Moyen / Medium",
    "urgence=2 - Moyenne / Medium",
    "Libelle=Incident Supervision – EvObserve {ev_id}",
]


def construire_bloc_symptome(sympt_var: str) -> list[str]:
    # Certains clients (formulaire, Swagger...) envoient la sequence
    # litterale antislash+n plutot qu'un vrai caractere de retour a la
    # ligne : on la normalise avant de decouper.
    normalise = sympt_var.replace("\\r\\n", "\n").replace("\\n", "\n").replace("\\r", "\n")
    premiere, *suite = SEPARATEUR_LIGNES.split(normalise)
    return [f"Symptome={premiere}", *suite]


def construire_corps_lignes(client: str, ev_id: str, sympt_var: str) -> list[str]:
    lignes = [ligne.format(client=client, ev_id=ev_id) for ligne in CORPS_LIGNES]
    lignes.extend(construire_bloc_symptome(sympt_var))
    return lignes
