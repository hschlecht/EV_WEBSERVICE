# EV Webservice - Mailer

Deux webservices independants, au meme contrat d'API (`POST /api/v1/mail`),
pour envoyer un mail texte brut a partir d'un client, d'un identifiant
EvObserve et d'un symptome :

- **`app.main`** : pilote le client **Outlook Desktop** installe sur le
  poste (Windows uniquement) via COM/pywin32.
- **`app.main_smtp`** : envoie directement par **SMTP**, avec la
  bibliotheque standard Python (`smtplib` + `email`), sans dependance a
  Outlook ni a un client de messagerie installe.

La construction du titre et du corps du mail est partagee entre les deux
(`app/message_builder.py`), seule la maniere d'envoyer differe.

## Installation

```bash
python -m venv .venv
source .venv/bin/activate  # ou .venv\Scripts\activate sous Windows
pip install -r requirements.txt
```

`pywin32` et `psutil` (necessaires uniquement a `app.main`, Outlook) ne
s'installent que sous Windows ; sur un autre OS, seul `app.main_smtp` est
utilisable.

---

## Option A - Webservice Outlook (`app.main`)

Pilote le client Outlook Desktop installe sur le poste. Au demarrage d'une
requete, le service verifie si Outlook est deja charge ; si ce n'est pas le
cas, il le lance automatiquement avant d'envoyer le message.

Pre-requis :
- Windows avec Microsoft Outlook Desktop installe et configure (un compte de
  messagerie doit deja etre configure dans Outlook).
- Sur le(s) poste(s) qui LISENT le mail recu (le compte destinataire), il
  faut desactiver l'option Outlook "Supprimer les sauts de ligne superflus
  dans les messages en texte brut" : Fichier > Options > Courrier > decocher
  cette case. Sans cela, Outlook fusionne automatiquement les lignes du
  corps du message qui ne sont pas separees par une ligne vide (comportement
  natif d'Outlook, independant de ce webservice).
- Sur le poste qui ENVOIE (celui qui execute le webservice), si le mail
  part malgre tout en HTML/RTF au lieu du texte brut, verifier dans Outlook :
  Fichier > Options > Courrier > "Lors de l'envoi de messages a un
  destinataire Exchange, toujours utiliser mon format par defaut au lieu du
  format du destinataire" > cocher cette case. Le webservice force aussi ce
  format directement via la propriete MAPI `PidTagMessageEditorFormat`,
  plus fiable que la seule propriete `BodyFormat` (voir
  `app/outlook_service.py`).

Lancement :

```powershell
uvicorn app.main:app --host 0.0.0.0 --port 8443
```

## Option B - Webservice SMTP (`app.main_smtp`)

Envoie le mail directement par SMTP (Office 365 / Exchange Online par
defaut), sans passer par Outlook.

Pre-requis : un compte SMTP capable d'envoyer des mails, avec ses
identifiants.

Configuration (variables d'environnement) :

| Variable        | Obligatoire | Defaut                 | Description                                 |
|------------------|:-----------:|-------------------------|------------------------------------------------|
| `SMTP_HOST`      | non         | `smtp.office365.com`    | Serveur SMTP                                    |
| `SMTP_PORT`      | non         | `587`                   | Port SMTP (STARTTLS)                            |
| `SMTP_USER`      | **oui**     | -                        | Compte utilise pour l'authentification SMTP     |
| `SMTP_PASSWORD`  | **oui**     | -                        | Mot de passe (ou mot de passe applicatif)       |
| `SMTP_FROM`      | non         | valeur de `SMTP_USER`   | Adresse d'expedition affichee                   |

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

Si le serveur SMTP est un relai interne sans authentification, adapter
`app/smtp_mail_service.py` pour retirer l'appel a `smtp.login(...)`.

Lancement :

```bash
uvicorn app.main_smtp:app --host 0.0.0.0 --port 8443
```

Le message est envoye en `Content-Type: text/plain` (via
`email.message.EmailMessage.set_content`), sans les problemes de fusion de
lignes propres a l'automatisation Outlook.

> Pour lancer les deux webservices en meme temps sur le meme poste,
> utiliser un port different pour l'un des deux (`--port 8444` par exemple).

---

## Envoyer un mail (POST /api/v1/mail)

Contrat identique pour les deux webservices. Le titre (objet) du mail est
genere automatiquement au format :

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

Reponse en cas de succes :

```json
{ "statut": "ok", "message": "Mail envoye a destinataire@exemple.com (titre: CASE OPENNING - TP BLOCHON - 26/09/2026 15:38:00)" }
```

En cas d'echec (Outlook indisponible/non configure pour `app.main`,
configuration SMTP manquante ou serveur injoignable pour `app.main_smtp`,
etc.), le service renvoie un code HTTP 502 avec le detail de l'erreur.

## Verification de sante

```bash
curl http://localhost:8443/api/v1/health
```

## Documentation interactive

FastAPI expose une documentation Swagger auto-generee, accessible une fois le
service demarre : http://localhost:8443/docs
