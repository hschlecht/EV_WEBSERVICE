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

Le titre (objet) du mail est genere automatiquement par le webservice au
format :

```
CASE OPENNING - <CLIENT> - JJ/MM/AAAA HH:MM:SS
```

Exemple pour le client `TP BLOCHON` le 26/09/2026 a 15:38:00 :

```
CASE OPENNING - TP BLOCHON - 26/09/2026 15:38:00
```

```bash
curl -X POST http://localhost:8443/api/v1/mail ^
  -H "Content-Type: application/json" ^
  -d "{\"adresse_mail\": \"destinataire@exemple.com\", \"client\": \"TP BLOCHON\"}"
```

En PowerShell :

```powershell
Invoke-RestMethod -Method Post -Uri "http://localhost:8443/api/v1/mail" `
  -ContentType "application/json" `
  -Body (@{ adresse_mail = "destinataire@exemple.com"; client = "TP BLOCHON" } | ConvertTo-Json)
```

Corps JSON attendu :

```json
{
  "adresse_mail": "destinataire@exemple.com",
  "client": "TP BLOCHON"
}
```

- `adresse_mail` (obligatoire) : adresse mail du destinataire.
- `client` (obligatoire) : nom du client, insere dans le titre et dans le corps genere.

Le corps du mail est lui aussi genere automatiquement, sur le modele
suivant (`Client` et `Adresse_site` sont remplaces par la valeur de
`client`) :

```
Centre_de_services=CDS-008
Service= CDSCAEN0017
Demandeur=28508
Client= TP BLOCHON
Adresse_site= TP BLOCHON
Equipe=EQ-0154
Intervenant=
ORIGINE=EVENEMENT
Dossier_interne=Supervision EvObserve - TRANSPORT BLOCHON MARTIN - BARIAU LECLERC
impact= 2 - Moyen / Medium
urgence=2 - Moyenne / Medium
Libelle=Incident Supervision – EvObserve ID    
Symptome=Ligne 1
Ligne 2
Ligne 3
Ligne 4
```

Reponse en cas de succes :

```json
{ "statut": "ok", "message": "Mail envoye a destinataire@exemple.com (titre: CASE OPENNING - TP BLOCHON - 26/09/2026 15:38:00)" }
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
