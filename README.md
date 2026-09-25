# EV Webservice - Mailer

Webservice qui envoie un email en texte brut directement par SMTP, avec
la bibliotheque standard Python (`smtplib` + `email`) : aucune dependance
a Outlook ou a un client de messagerie installe sur le poste.

Pre-requis :
- Python 3.10+.
- Un compte SMTP capable d'envoyer des mails (par defaut : Office 365 /
  Exchange Online, `smtp.office365.com:587`), avec ses identifiants.

## Installation

```bash
python -m venv .venv
source .venv/bin/activate  # ou .venv\Scripts\activate sous Windows
pip install -r requirements.txt
```

## Configuration (variables d'environnement)

| Variable        | Obligatoire | Defaut                 | Description                                 |
|------------------|:-----------:|-------------------------|----------------------------------------------|
| `SMTP_HOST`      | non         | `smtp.office365.com`    | Serveur SMTP                                  |
| `SMTP_PORT`      | non         | `587`                   | Port SMTP (STARTTLS)                          |
| `SMTP_USER`      | **oui**     | -                        | Compte utilise pour l'authentification SMTP   |
| `SMTP_PASSWORD`  | **oui**     | -                        | Mot de passe (ou mot de passe applicatif)     |
| `SMTP_FROM`      | non         | valeur de `SMTP_USER`   | Adresse d'expedition affichee                 |

Exemple (Linux/macOS) :

```bash
export SMTP_USER="moi@monentreprise.com"
export SMTP_PASSWORD="mot-de-passe-applicatif"
```

Exemple (PowerShell) :

```powershell
$env:SMTP_USER = "moi@monentreprise.com"
$env:SMTP_PASSWORD = "mot-de-passe-applicatif"
```

Si ton serveur SMTP est un relai interne sans authentification, mets
`SMTP_USER`/`SMTP_PASSWORD` a une valeur non vide quand meme (la
verification ne fait que s'assurer que les variables sont definies) ou
adapte `app/mail_service.py` pour retirer l'appel a `smtp.login(...)`.

## Lancement du webservice

```bash
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
curl -X POST http://localhost:8443/api/v1/mail \
  -H "Content-Type: application/json" \
  -d '{"adresse_mail": "destinataire@exemple.com", "client": "TP BLOCHON", "ev_id": "987654", "sympt_var": "Ligne A\nLigne B\nLigne C"}'
```

En PowerShell :

```powershell
Invoke-RestMethod -Method Post -Uri "http://localhost:8443/api/v1/mail" `
  -ContentType "application/json" `
  -Body (@{ adresse_mail = "destinataire@exemple.com"; client = "TP BLOCHON"; ev_id = "987654"; sympt_var = "Ligne A`nLigne B`nLigne C" } | ConvertTo-Json)
```

Corps JSON attendu :

```json
{
  "adresse_mail": "destinataire@exemple.com",
  "client": "TP BLOCHON",
  "ev_id": "987654",
  "sympt_var": "Ligne A\nLigne B\nLigne C"
}
```

- `adresse_mail` (obligatoire) : adresse mail du destinataire.
- `client` (obligatoire) : nom du client, insere dans le titre et dans le corps genere.
- `ev_id` (obligatoire) : identifiant EvObserve, insere dans la ligne `Libelle` du corps.
- `sympt_var` (obligatoire) : contenu de la ligne `Symptome`. Peut contenir
  plusieurs lignes (separees par `\n` dans le JSON) : chaque ligne devient
  une ligne distincte du corps, la premiere etant precedee de `Symptome=`.

Le corps du mail est lui aussi genere automatiquement, sur le modele
suivant (`Client`, `Adresse_site` et `Dossier_interne` sont remplaces par
la valeur de `client`, `ev_id` remplace `ID` dans `Libelle`, et `sympt_var`
alimente `Symptome`) :

```
Centre_de_services=CDS-008
Service= CDSCAEN0017
Demandeur=28508
Client= TP BLOCHON
Adresse_site= TP BLOCHON
Equipe=EQ-0154
Intervenant=
ORIGINE=EVENEMENT
Dossier_interne=Supervision EvObserve - TP BLOCHON
impact= 2 - Moyen / Medium
urgence=2 - Moyenne / Medium
Libelle=Incident Supervision – EvObserve 987654
Symptome=Ligne A
Ligne B
Ligne C
```

Le message est envoye en `Content-Type: text/plain` (via
`email.message.EmailMessage.set_content`), sans les problemes de fusion de
lignes propres a l'automatisation Outlook.

Reponse en cas de succes :

```json
{ "statut": "ok", "message": "Mail envoye a destinataire@exemple.com (titre: CASE OPENNING - TP BLOCHON - 26/09/2026 15:38:00)" }
```

En cas d'echec (configuration SMTP manquante, authentification refusee,
serveur injoignable, etc.), le service renvoie un code HTTP 502 avec le
detail de l'erreur.

## Verification de sante

```bash
curl http://localhost:8443/api/v1/health
```

## Documentation interactive

FastAPI expose une documentation Swagger auto-generee, accessible une fois le
service demarre : http://localhost:8443/docs
