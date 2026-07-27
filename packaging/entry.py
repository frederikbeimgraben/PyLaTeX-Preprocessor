"""PyInstaller entry script for the standalone `pytex` binary.

This module only calls `main` from the CLI, so the frozen binary behaves in
the same way as the `pytex` console script.
"""

import sys

from pytex_builder.build import main

if __name__ == "__main__":
    sys.exit(main())
