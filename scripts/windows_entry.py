"""Entrada del ejecutable: GUI normal o comprobación empaquetada con datos ficticios."""

import sys
from pathlib import Path

from vaultlab.app import main

if __name__ == "__main__":
    if len(sys.argv) == 3 and sys.argv[1] == "--self-test":
        from vaultlab.packaging_checks import run_self_test

        sys.exit(run_self_test(Path(sys.argv[2])))
    main()
