"""Webservice FastAPI exposant l'envoi de mail via Outlook Desktop.

Lancement : uvicorn app.main:app --host 0.0.0.0 --port 8443
"""

import logging
from datetime import datetime

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, EmailStr, Field

from app.outlook_service import OutlookError, send_mail

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("ev_webservice")

app = FastAPI(title="EV Webservice - Outlook Mailer")


class MailRequest(BaseModel):
    adresse_mail: EmailStr = Field(..., description="Adresse mail du destinataire")
    client: str = Field(..., min_length=1, description="Nom du client (VAR_1 du titre et du corps)")


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
    "Libelle=Incident Supervision – EvObserve ID",
    "Symptome=Ligne 1",
    "Ligne 2",
    "Ligne 3",
    "Ligne 4",
]


def construire_corps(client: str) -> str:
    # \r\n explicite : un simple \n peut etre "aplati" par Outlook (mode
    # plain text "format=flowed"), ce qui fusionne des lignes consecutives.
    return "\r\n".join(ligne.format(client=client) for ligne in CORPS_LIGNES)


@app.post("/api/v1/mail", response_model=MailResponse)
def envoyer_mail(requete: MailRequest) -> MailResponse:
    titre = construire_titre(requete.client)
    corps = construire_corps(requete.client)
    try:
        send_mail(
            destinataire=requete.adresse_mail,
            titre=titre,
            corps=corps,
        )
    except OutlookError as exc:
        logger.exception("Echec de l'envoi du mail")
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    return MailResponse(statut="ok", message=f"Mail envoye a {requete.adresse_mail} (titre: {titre})")


@app.get("/api/v1/health")
def health() -> dict:
    return {"statut": "ok"}
