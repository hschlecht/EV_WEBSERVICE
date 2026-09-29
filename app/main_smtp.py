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

from fastapi import FastAPI, HTTPException, Request

from app.affichage import afficher_appel_entrant, afficher_message, afficher_requete, securiser_encodage_console
from app.json_repair import reparer_backslashes_json
from app.message_builder import MailRequest, MailResponse, construire_corps_lignes, construire_titre
from app.smtp_mail_service import MailError, send_mail

securiser_encodage_console()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("ev_webservice_smtp")

MODE_DEBUG = os.environ.get("EV_WEBSERVICE_DEBUG", "").strip().lower() in {"1", "true", "vrai", "oui", "yes"}

app = FastAPI(title="EV Webservice - SMTP Mailer")


@app.middleware("http")
async def journaliser_et_reparer_appel_entrant(request: Request, call_next):
    """A chaque appel :
    1. En mode debug, journalise l'arrivee de l'appel (methode, chemin,
       client) et le JSON brut recu, avant toute validation Pydantic -
       utile pour diagnostiquer une requete malformee.
    2. Repare les antislash isoles (non echappes) dans le corps JSON, par
       exemple un chemin Windows du type "C:\\Label" insere tel quel par
       une sonde de supervision sans echapper l'antislash : sans ce
       correctif, le JSON est invalide et la requete est rejetee (422)
       avant meme d'atteindre notre logique metier (voir
       app/json_repair.py).
    """
    corps_brut = await request.body()

    if MODE_DEBUG:
        client = f"{request.client.host}:{request.client.port}" if request.client else "inconnu"
        afficher_appel_entrant(logger, request.method, request.url.path, client, corps_brut)

    if corps_brut:
        texte_brut = corps_brut.decode("utf-8", errors="replace")
        texte_repare = reparer_backslashes_json(texte_brut)
        if texte_repare != texte_brut:
            if MODE_DEBUG:
                logger.info("JSON corrige automatiquement (antislash isole echappe) :\n%s", texte_repare)
            request._body = texte_repare.encode("utf-8")  # noqa: SLF001 - relecture par le parsing JSON suivant

    return await call_next(request)


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
    if MODE_DEBUG:
        afficher_requete(logger, requete)
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
