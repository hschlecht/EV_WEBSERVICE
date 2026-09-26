# EV Webservice - Mailer

Deux webservices independants, au meme contrat d'API (`POST /api/v1/mail`),
pour envoyer un mail texte brut dont le corps est construit dynamiquement
a partir de variables (centre de services, service, demandeur, client,
adresse, libelle, symptome) :

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

Envoie le mail directement par SMTP. Par defaut, aucune authentification
ni TLS n'est utilisee (cas d'un relai SMTP interne, souvent sur le port
25) ; l'authentification (avec STARTTLS) reste disponible si le serveur
en a besoin (ex: Office 365 / Exchange Online).

Configuration (variables d'environnement) :

| Variable        | Obligatoire | Defaut  | Description                                                        |
|------------------|:-----------:|----------|----------------------------------------------------------------------|
| `SMTP_HOST`      | **oui**     | -        | Serveur/relai SMTP                                                    |
| `SMTP_PORT`      | non         | `25`     | Port SMTP                                                             |
| `SMTP_FROM`      | **oui**\*   | -        | Adresse d'expedition (\*= facultatif si `SMTP_USER` est defini)       |
| `SMTP_USE_TLS`   | non         | `false`  | `true` pour utiliser STARTTLS avant l'envoi                           |
| `SMTP_USER`      | non         | -        | Compte pour l'authentification SMTP (omis = pas d'authentification)  |
| `SMTP_PASSWORD`  | non\*\*     | -        | Mot de passe (\*\*= obligatoire si `SMTP_USER` est defini)            |

Relai interne sans authentification (cas le plus courant en entreprise) :

```bash
export SMTP_HOST="relai-smtp.monentreprise.local"
export SMTP_FROM="service@monentreprise.com"
```

Serveur avec authentification (ex. Office 365) :

```bash
export SMTP_HOST="smtp.office365.com"
export SMTP_PORT="587"
export SMTP_USE_TLS="true"
export SMTP_USER="moi@monentreprise.com"
export SMTP_PASSWORD="mot-de-passe-applicatif"
```

Exemple (PowerShell) :

```powershell
$env:SMTP_HOST = "relai-smtp.monentreprise.local"
$env:SMTP_FROM = "service@monentreprise.com"
```

### Alternative : fichier de configuration `config.env`

Plutot que des variables d'environnement, ces valeurs peuvent etre
declarees dans un fichier `config.env` a la racine du projet (charge
automatiquement au demarrage, voir `app/config.py`) :

```bash
cp config.env.example config.env
```

Puis editer `config.env` :

```
SMTP_HOST=relai-smtp.monentreprise.local
SMTP_FROM=service@monentreprise.com
```

`config.env` est ignore par git (voir `.gitignore`) : il ne sera jamais
commite. Une variable d'environnement deja definie avant le lancement du
webservice reste prioritaire sur le contenu de ce fichier.

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
CASE OPENNING - <VAR_CLIENT> - JJ/MM/AAAA HH:MM:SS
```

```bash
curl -X POST http://localhost:8443/api/v1/mail \
  -H "Content-Type: application/json" \
  -d '{"adresse_mail": "destinataire@exemple.com", "var_cds": "CDS-008", "var_service": "CDSCAEN0393", "var_demandeur": "66502", "var_client": "GIP LABEO [GIP LABEO]", "var_adresse": "GIP LABEO [GIP LABEO]", "var_libelle": "LABEO Morning check - 2026/39 - 24-09-2026", "var_symptome": "LABEO Morning check - 2026/39 - 24-09-2026"}'
```

En PowerShell :

```powershell
Invoke-RestMethod -Method Post -Uri "http://localhost:8443/api/v1/mail" `
  -ContentType "application/json" `
  -Body (@{
    adresse_mail = "destinataire@exemple.com"
    var_cds = "CDS-008"
    var_service = "CDSCAEN0393"
    var_demandeur = "66502"
    var_client = "GIP LABEO [GIP LABEO]"
    var_adresse = "GIP LABEO [GIP LABEO]"
    var_libelle = "LABEO Morning check - 2026/39 - 24-09-2026"
    var_symptome = "LABEO Morning check - 2026/39 - 24-09-2026"
  } | ConvertTo-Json)
```

Corps JSON attendu :

```json
{
  "adresse_mail": "destinataire@exemple.com",
  "var_cds": "CDS-008",
  "var_service": "CDSCAEN0393",
  "var_demandeur": "66502",
  "var_client": "GIP LABEO [GIP LABEO]",
  "var_adresse": "GIP LABEO [GIP LABEO]",
  "var_libelle": "LABEO Morning check - 2026/39 - 24-09-2026",
  "var_symptome": "LABEO Morning check - 2026/39 - 24-09-2026"
}
```

- `adresse_mail` (obligatoire) : adresse mail du destinataire.
- `var_cds` (obligatoire) : alimente `Centre_de_services`.
- `var_service` (obligatoire) : alimente `Service`.
- `var_demandeur` (obligatoire) : alimente `Demandeur`.
- `var_client` (obligatoire) : alimente `Client`, et le titre du mail.
- `var_adresse` (obligatoire) : alimente `Adresse_site`.
- `var_libelle` (obligatoire) : alimente `Libelle`.
- `var_symptome` (obligatoire) : alimente `Symptome`. Peut contenir
  plusieurs lignes (separees par `\n` dans le JSON) : chaque ligne devient
  une ligne distincte du corps, la premiere etant precedee de `Symptome=`.

`Equipe`, `Intervenant`, `ORIGINE`, `Dossier_interne`, `impact` et
`urgence` restent des valeurs fixes dans le corps genere (non
parametrables pour l'instant).

Le corps du mail est genere automatiquement, sur le modele suivant :

```
Centre_de_services=CDS-008
Service=CDSCAEN0393
Demandeur=66502
Client=GIP LABEO [GIP LABEO]
Adresse_site=GIP LABEO [GIP LABEO]
Equipe=EQ-0154
Intervenant=
ORIGINE=EMAIL
Dossier_interne=06ad802324a87214306c3b04d9acf7747fdf86af
impact=1 - Faible / Low
urgence=1 - Faible / Low
Libelle=LABEO Morning check - 2026/39 - 24-09-2026
Symptome=LABEO Morning check - 2026/39 - 24-09-2026
```

Reponse en cas de succes :

```json
{ "statut": "ok", "message": "Mail envoye a destinataire@exemple.com (titre: CASE OPENNING - GIP LABEO [GIP LABEO] - 26/09/2026 06:13:21)" }
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
