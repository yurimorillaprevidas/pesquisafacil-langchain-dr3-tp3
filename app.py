"""Entrada principal: python app.py [--demo | --pergunta TEXTO]."""

import sys

from pesquisafacil.cli import main

if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
    raise SystemExit(main())
