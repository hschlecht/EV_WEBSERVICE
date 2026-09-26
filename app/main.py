"""Webservice FastAPI exposant l'envoi de mail via Outlook Desktop.

Lancement : uvicorn app.main:app --host 0.0.0.0 --port 8443
"""

import logging

from fastapi import FastAPI, HTTPException

from app.message_builder import MailRequest, MailResponse, construire_corps_lignes, construire_titre
from app.outlook_service import OutlookError, send_mail

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("ev_webservice")

app = FastAPI(title="EV Webservice - Outlook Mailer")


def construire_corps(requete: MailRequest) -> str:
    # \r\n explicite : un simple \n peut etre "aplati" par Outlook (mode
    # plain text "format=flowed"), ce qui fusionne des lignes consecutives.
    lignes = construire_corps_lignes(
        var_cds=requete.var_cds,
        var_service=requete.var_service,
        var_demandeur=requete.var_demandeur,
        var_client=requete.var_client,
        var_adresse=requete.var_adresse,
        var_libelle=requete.var_libelle,
        var_symptome=requete.var_symptome,
    )
    return "\r\n".join(lignes)


@app.post("/api/v1/mail", response_model=MailResponse)
def envoyer_mail(requete: MailRequest) -> MailResponse:
    titre = construire_titre(requete.var_client)
    corps = construire_corps(requete)
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
