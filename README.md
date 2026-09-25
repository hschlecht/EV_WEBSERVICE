# EV Webservice - Outlook Mailer

Webservice local (Windows uniquement) qui pilote le client Outlook Desktop
installe sur le poste pour envoyer un email. Au demarrage d'une requete, le
service verifie si Outlook est deja charge ; si ce n'est pas le cas, il le
lance automatiquement avant d'envoyer le message.

Pre-requis :
- Windows avec Microsoft Outlook Desktop installe et configure (un compte de
  messagerie doit deja etre configure dans Outlook).
- Python 3.10+.

## Installation

```powershell
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

## Lancement du webservice

```powershell
uvicorn app.main:app --host 0.0.0.0 --port 8443
```

Le service ecoute en HTTP (pas de TLS) sur le port 8443, sur le chemin
`/api/v1/mail`.

## Envoyer un mail (POST)

```bash
curl -X POST http://localhost:8443/api/v1/mail ^
  -H "Content-Type: application/json" ^
  -d "{\"adresse_mail\": \"destinataire@exemple.com\", \"titre_message\": \"Mon titre de message\"}"
```

En PowerShell :

```powershell
Invoke-RestMethod -Method Post -Uri "http://localhost:8443/api/v1/mail" `
  -ContentType "application/json" `
  -Body (@{ adresse_mail = "destinataire@exemple.com"; titre_message = "Mon titre de message" } | ConvertTo-Json)
```

Corps JSON attendu :

```json
{
  "adresse_mail": "destinataire@exemple.com",
  "titre_message": "Mon titre de message",
  "corps_message": "Texte optionnel du mail"
}
```

- `adresse_mail` (obligatoire) : adresse mail du destinataire.
- `titre_message` (obligatoire) : objet du mail.
- `corps_message` (optionnel) : corps du mail, vide par defaut.

Reponse en cas de succes :

```json
{ "statut": "ok", "message": "Mail envoye a destinataire@exemple.com" }
```

En cas d'echec (Outlook indisponible, non configure, etc.), le service
renvoie un code HTTP 502 avec le detail de l'erreur.

## Verification de sante

```bash
curl http://localhost:8443/api/v1/health
```

## Documentation interactive

FastAPI expose une documentation Swagger auto-generee, accessible une fois le
service demarre : http://localhost:8443/docs
