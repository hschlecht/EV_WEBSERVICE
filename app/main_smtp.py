"""Webservice FastAPI exposant l'envoi de mail via SMTP.

Lancement normal (aucun detail affiche en console) :
    python run.py --host 0.0.0.0 --port 8443

Lancement en mode debug (titre + corps du message affiches avant
envoi) :
    python run.py --debug --host 0.0.0.0 --port 8443

Le mode debug est pilote par la variable d'environnement
EV_WEBSERVICE_DEBUG (positionnee par run.py), et non par un argument de
la ligne de commande uvicorn directement.
"""

import logging
import os

from fastapi import FastAPI, HTTPException

from app.affichage import afficher_message, securiser_encodage_console
from app.message_builder import MailRequest, MailResponse, construire_corps_lignes, construire_titre
from app.smtp_mail_service import MailError, send_mail

securiser_encodage_console()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("ev_webservice_smtp")

MODE_DEBUG = os.environ.get("EV_WEBSERVICE_DEBUG", "").strip().lower() in {"1", "true", "vrai", "oui", "yes"}

app = FastAPI(title="EV Webservice - SMTP Mailer")


def construire_corps(requete: MailRequest) -> str:
    lignes = construire_corps_lignes(
        var_cds=requete.var_cds,
        var_service=requete.var_service,
        var_demandeur=requete.var_demandeur,
        var_client=requete.var_client,
        var_adresse=requete.var_adresse,
        var_intervenant=requete.var_intervenant,
        var_libelle=requete.var_libelle,
        var_symptome=requete.var_symptome,
    )
    return "\r\n".join(lignes)


@app.post("/api/v1/mail", response_model=MailResponse)
def envoyer_mail(requete: MailRequest) -> MailResponse:
    titre = construire_titre(requete.var_client)
    corps = construire_corps(requete)
    if MODE_DEBUG:
        afficher_message(logger, titre, corps)
    try:
        send_mail(
            destinataire=requete.adresse_mail,
            titre=titre,
            corps=corps,
        )
    except MailError as exc:
        logger.exception("Echec de l'envoi du mail")
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    return MailResponse(statut="ok", message=f"Mail envoye a {requete.adresse_mail} (titre: {titre})")


@app.get("/api/v1/health")
def health() -> dict:
    return {"statut": "ok"}
