"""PyInstaller entry point for the standalone `pytex` binary.

Thin wrapper around the CLI's ``main`` so the frozen executable behaves exactly
like the ``pytex`` console script.
"""

import sys

from pytex_builder.build import main

if __name__ == "__main__":
    sys.exit(main())
