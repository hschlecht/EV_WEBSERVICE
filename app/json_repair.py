"""Reparation d'un JSON dont les chaines contiennent des antislash non
echappes.

Cas reel vise : une sonde de supervision (ex. verification de disque
Windows) renvoie un texte contenant un chemin du type "C:\\Label", et ce
texte est insere tel quel dans le JSON transmis a l'API sans que
l'antislash ne soit double (\\\\). Un antislash JSON valide ne peut etre
suivi que de ", \\, /, b, f, n, r, t, u ; tout antislash suivi d'un autre
caractere (espace, lettre...) rend le JSON invalide et le fait rejeter
par le parseur (422 Unprocessable Entity), avant meme d'atteindre notre
logique metier.

Ce module repare ce cas precis : il double tout antislash "isole" (non
suivi d'un caractere d'echappement JSON valide) trouve a l'interieur
d'une chaine JSON, sans toucher aux antislash deja valides.
"""

from __future__ import annotations

ECHAPPEMENTS_VALIDES = set('"\\/bfnrtu')


def reparer_backslashes_json(texte: str) -> str:
    """Double les antislash isoles (non suivis d'un caractere
    d'echappement JSON valide) presents a l'interieur des chaines du
    texte JSON donne. Les antislash deja valides (\\\\, \\n, \\", ...)
    sont laisses inchanges."""
    resultat: list[str] = []
    en_chaine = False
    i = 0
    n = len(texte)

    while i < n:
        caractere = texte[i]

        if en_chaine and caractere == "\\":
            suivant = texte[i + 1] if i + 1 < n else ""
            if suivant in ECHAPPEMENTS_VALIDES:
                resultat.append(caractere)
                resultat.append(suivant)
                i += 2
            else:
                # Antislash isole (ex: chemin Windows C:\Label) : on le
                # double pour en faire un antislash JSON valide.
                resultat.append("\\\\")
                i += 1
            continue

        if caractere == '"':
            en_chaine = not en_chaine

        resultat.append(caractere)
        i += 1

    return "".join(resultat)
