"""Lanceur du webservice SMTP, avec une option --debug.

Sans --debug : aucun detail (titre/corps du message) n'est affiche en
console. Avec --debug : le titre et le corps de chaque message sont
affiches avant envoi (voir app/affichage.py).

Exemples :
    python run.py --host 0.0.0.0 --port 8443
    python run.py --debug --host 0.0.0.0 --port 8443
"""

from __future__ import annotations

import argparse
import os

import uvicorn


def analyser_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Webservice EV Mailer (SMTP)")
    parser.add_argument("--host", default="0.0.0.0", help="Adresse d'ecoute (defaut: 0.0.0.0)")
    parser.add_argument("--port", type=int, default=8443, help="Port d'ecoute (defaut: 8443)")
    parser.add_argument(
        "-d", "--debug", action="store_true", help="Affiche en console le titre et le corps de chaque message"
    )
    return parser.parse_args()


def main() -> None:
    args = analyser_arguments()
    os.environ["EV_WEBSERVICE_DEBUG"] = "1" if args.debug else "0"

    uvicorn.run("app.main_smtp:app", host=args.host, port=args.port)


if __name__ == "__main__":
    main()
