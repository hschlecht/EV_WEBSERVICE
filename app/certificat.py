"""Generation d'un certificat TLS auto-signe (pour HTTPS local/interne).

Le certificat et sa cle privee sont generes une seule fois (a la racine
du projet, dossier certs/) et reutilises aux lancements suivants tant
qu'ils existent. Ce dossier est ignore par git : la cle privee n'est
jamais commitee.
"""

from __future__ import annotations

import datetime
import ipaddress
from pathlib import Path

from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.x509.oid import NameOID

RACINE_PROJET = Path(__file__).resolve().parent.parent
DOSSIER_CERTS = RACINE_PROJET / "certs"
FICHIER_CERT = DOSSIER_CERTS / "cert.pem"
FICHIER_CLE = DOSSIER_CERTS / "key.pem"

DUREE_VALIDITE_JOURS = 3650  # 10 ans


def assurer_certificat_autosigne(
    fichier_cert: Path = FICHIER_CERT, fichier_cle: Path = FICHIER_CLE
) -> tuple[Path, Path]:
    """Retourne (cert, cle) : genere une paire auto-signee si absente."""
    if fichier_cert.is_file() and fichier_cle.is_file():
        return fichier_cert, fichier_cle

    fichier_cert.parent.mkdir(parents=True, exist_ok=True)

    cle_privee = rsa.generate_private_key(public_exponent=65537, key_size=2048)

    sujet = emetteur = x509.Name(
        [x509.NameAttribute(NameOID.COMMON_NAME, "EV Webservice (certificat auto-signe)")]
    )

    maintenant = datetime.datetime.now(datetime.timezone.utc)
    certificat = (
        x509.CertificateBuilder()
        .subject_name(sujet)
        .issuer_name(emetteur)
        .public_key(cle_privee.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(maintenant - datetime.timedelta(days=1))
        .not_valid_after(maintenant + datetime.timedelta(days=DUREE_VALIDITE_JOURS))
        .add_extension(
            x509.SubjectAlternativeName(
                [
                    x509.DNSName("localhost"),
                    x509.IPAddress(ipaddress.ip_address("127.0.0.1")),
                    x509.IPAddress(ipaddress.ip_address("0.0.0.0")),
                ]
            ),
            critical=False,
        )
        .sign(cle_privee, hashes.SHA256())
    )

    fichier_cle.write_bytes(
        cle_privee.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.TraditionalOpenSSL,
            encryption_algorithm=serialization.NoEncryption(),
        )
    )
    fichier_cert.write_bytes(certificat.public_bytes(serialization.Encoding.PEM))

    return fichier_cert, fichier_cle
