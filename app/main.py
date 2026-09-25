"""Webservice FastAPI exposant l'envoi de mail via Outlook Desktop.

Lancement : uvicorn app.main:app --host 0.0.0.0 --port 8443
"""

import logging

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, EmailStr, Field

from app.outlook_service import OutlookError, send_mail

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("ev_webservice")

app = FastAPI(title="EV Webservice - Outlook Mailer")


class MailRequest(BaseModel):
    adresse_mail: EmailStr = Field(..., description="Adresse mail du destinataire")
    titre_message: str = Field(..., min_length=1, description="Titre (objet) du message")
    corps_message: str = Field("", description="Corps du message (optionnel)")


class MailResponse(BaseModel):
    statut: str
    message: str


@app.post("/api/v1/mail", response_model=MailResponse)
def envoyer_mail(requete: MailRequest) -> MailResponse:
    try:
        send_mail(
            destinataire=requete.adresse_mail,
            titre=requete.titre_message,
            corps=requete.corps_message,
        )
    except OutlookError as exc:
        logger.exception("Echec de l'envoi du mail")
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    return MailResponse(statut="ok", message=f"Mail envoye a {requete.adresse_mail}")


@app.get("/api/v1/health")
def health() -> dict:
    return {"statut": "ok"}
