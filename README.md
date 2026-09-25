# EV Webservice - Outlook Mailer

Webservice local (Windows uniquement) qui pilote le client Outlook Desktop
installe sur le poste pour envoyer un email. Au demarrage d'une requete, le
service verifie si Outlook est deja charge ; si ce n'est pas le cas, il le
lance automatiquement avant d'envoyer le message.

Pre-requis :
- Windows avec Microsoft Outlook Desktop installe et configure (un compte de
  messagerie doit deja etre configure dans Outlook).
- Python 3.10+.
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
  format du destinataire" > cocher cette case. Outlook peut en effet
  reprendre le format prefere du destinataire (carnet d'adresses/Exchange)
  et l'imposer malgre le format texte brut demande par le webservice.
  Le webservice force aussi ce format directement via la propriete MAPI
  `PidTagMessageEditorFormat`, plus fiable que la seule propriete
  `BodyFormat` (voir `app/outlook_service.py`).

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
  -d "{\"adresse_mail\": \"destinataire@exemple.com\", \"client\": \"TP BLOCHON\", \"ev_id\": \"987654\", \"sympt_var\": \"Ligne A\\nLigne B\\nLigne C\"}"
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

Chaque ligne du corps est jointe avec un retour a la ligne CRLF explicite
(`\r\n`), pour eviter qu'Outlook ne fusionne des lignes consecutives lors
de l'envoi en texte brut.

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
