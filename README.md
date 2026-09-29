# EV Webservice - Mailer

Webservice qui envoie un mail en texte brut directement par SMTP (avec la
bibliotheque standard Python `smtplib` + `email`), dont le corps est
construit dynamiquement a partir de variables (centre de services,
service, demandeur, client, adresse, libelle, symptome).

## Installation

**Linux / macOS :**

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Si `python3 -m venv` echoue avec une erreur du type `ensurepip is not
available` (frequent sur Debian/Ubuntu), installer d'abord le paquet
systeme correspondant :

```bash
sudo apt install python3-venv
```

**Windows :**

```powershell
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

## Configuration SMTP

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

## Lancement du webservice

```bash
python run.py --host 0.0.0.0 --port 8443
```

Ajouter `--debug` (ou `-d`) pour afficher en console le titre et le
corps de chaque message avant envoi (utile pour verifier le contenu
transmis) :

```bash
python run.py --debug --host 0.0.0.0 --port 8443
```

Sans `--debug` (par defaut), aucun detail du message n'est affiche en
console.

### HTTPS (certificat auto-signe)

Par defaut, le webservice ecoute en **HTTPS** sur le port 8443, avec un
certificat auto-signe genere automatiquement au premier lancement
(`certs/cert.pem` et `certs/key.pem`, ignores par git — la cle privee
n'est jamais commitee). Les lancements suivants reutilisent ce meme
certificat (valide 10 ans).

Un certificat auto-signe n'etant reconnu par aucune autorite, les clients
doivent explicitement ignorer l'avertissement de securite :
- `curl` : ajouter `-k` (ou `--insecure`).
- PowerShell `Invoke-RestMethod` : ajouter `-SkipCertificateCheck`
  (PowerShell 7+) ou utiliser `[System.Net.ServicePointManager]::ServerCertificateValidationCallback = {$true}`
  au prealable (Windows PowerShell 5.1).
- Navigateur : accepter manuellement l'avertissement ("Continuer vers ce site").

Pour desactiver HTTPS et revenir en HTTP simple :

```bash
python run.py --no-https --host 0.0.0.0 --port 8443
```

Le message est construit manuellement en MIME multipart
minimal :

```
Subject: ...
Cc: herve.schlecht@axians.com
MIME-Version: 1.0
Content-Type: multipart/mixed; boundary="..."

--<boundary>
Content-Type: text/plain; charset="us-ascii"
Content-Transfer-Encoding: 7bit

<corps>

--<boundary>--
```

Construit "a la main" (pas de `email.mime`/`email.message.EmailMessage`)
pour reproduire exactement le formatage d'un message de reference traite
correctement par le systeme receveur, et eviter tout encodage
(quoted-printable/base64) qui alterait les caracteres `=` du corps. En
consequence, **le titre et le corps doivent rester strictement en ASCII**
(pas d'accent, pas de tiret demi-cadratin `–`) — un caractere non-ASCII
fait echouer l'envoi avec une erreur explicite
plutot que de produire un message mal forme.

## Envoyer un mail (POST /api/v1/mail)

Le titre (objet) du mail est genere automatiquement au format :

```
[AXIANS] CASE OPENNING - <VAR_CLIENT> - JJ/MM/AAAA HH:MM:SS
```

```bash
curl -k -X POST https://localhost:8443/api/v1/mail \
  -H "Content-Type: application/json" \
  -d '{"adresse_mail": "destinataire@exemple.com", "var_cds": "CDS-008", "var_service": "CDSCAEN0393", "var_demandeur": "66502", "var_client": "GIP LABEO [GIP LABEO]", "var_adresse": "GIP LABEO [GIP LABEO]", "var_intervenant": 12345, "var_libelle": "LABEO Morning check - 2026/39 - 24-09-2026", "var_symptome": "LABEO Morning check - 2026/39 - 24-09-2026"}'
```

En PowerShell :

```powershell
Invoke-RestMethod -Method Post -Uri "https://localhost:8443/api/v1/mail" -SkipCertificateCheck `
  -ContentType "application/json" `
  -Body (@{
    adresse_mail = "destinataire@exemple.com"
    var_cds = "CDS-008"
    var_service = "CDSCAEN0393"
    var_demandeur = "66502"
    var_client = "GIP LABEO [GIP LABEO]"
    var_adresse = "GIP LABEO [GIP LABEO]"
    var_intervenant = 12345
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
  "var_intervenant": 12345,
  "var_libelle": "LABEO Morning check - 2026/39 - 24-09-2026",
  "var_symptome": "LABEO Morning check - 2026/39 - 24-09-2026"
}
```

- `adresse_mail` (obligatoire) : adresse mail du destinataire. `herve.schlecht@axians.com` est systematiquement mis en copie (Cc) de chaque envoi.
- `var_cds` (obligatoire) : alimente `Centre_de_services`.
- `var_service` (obligatoire) : alimente `Service`.
- `var_demandeur` (obligatoire) : alimente `Demandeur`.
- `var_client` (obligatoire) : alimente `Client`, et le titre du mail.
- `var_adresse` (obligatoire) : alimente `Adresse_site`.
- `var_intervenant` (optionnel, valeur decimale, vide par defaut) : alimente `Intervenant`.
- `var_libelle` (obligatoire) : alimente `Libelle`.
- `var_symptome` (obligatoire) : alimente `Symptome`. Peut contenir
  plusieurs lignes (separees par `\n` dans le JSON) : chaque ligne devient
  une ligne distincte du corps, la premiere etant precedee de `Symptome=`.

`Equipe`, `ORIGINE`, `Dossier_interne`, `impact` et `urgence` restent des
valeurs fixes dans le corps genere (non parametrables pour l'instant).

Le corps du mail est genere automatiquement, sur le modele suivant :

```
Service=CDSCAEN0393
Demandeur=66502
Client=GIP LABEO [GIP LABEO]
Adresse_site=GIP LABEO [GIP LABEO]
Centre_de_services=CDS-008
Equipe=EQ-0154
Intervenant=12345
ORIGINE=EMAIL
Dossier_interne=06ad802324a87214306c3b04d9acf7747fdf86af
impact=1 - Faible / Low
urgence=1 - Faible / Low
Libelle=LABEO Morning check - 2026/39 - 24-09-2026
Symptome=LABEO Morning check - 2026/39 - 24-09-2026
```

Reponse en cas de succes :

```json
{ "statut": "ok", "message": "Mail envoye a destinataire@exemple.com (titre: [AXIANS] CASE OPENNING - GIP LABEO [GIP LABEO] - 26/09/2026 06:13:21)" }
```

En cas d'echec (configuration SMTP manquante, serveur injoignable,
authentification refusee, etc.), le service renvoie un code HTTP 502
avec le detail de l'erreur.

## Verification de sante

```bash
curl -k https://localhost:8443/api/v1/health
```

## Documentation interactive

FastAPI expose une documentation Swagger auto-generee, accessible une fois le
service demarre : https://localhost:8443/docs (apres avoir accepte l'avertissement de securite dans le navigateur)
