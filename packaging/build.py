"""Build the standalone `pytex` binary with PyInstaller.

    python packaging/build.py

Installs PyInstaller and the bundle.toml `requirements` into the current
environment, then freezes the binary into `dist/pytex` (use a fresh virtualenv;
this mutates the active one). `pytex` itself must already be installed (e.g.
`pip install -e .`).
"""

from __future__ import annotations

import subprocess
import sys
import tomllib
from pathlib import Path

_HERE = Path(__file__).resolve().parent
_SPEC = _HERE / "pytex.spec"


def main() -> int:
    bundle = tomllib.loads((_HERE / "bundle.toml").read_text())
    requirements: list[str] = bundle["bundle"]["requirements"]

    subprocess.run(
        [sys.executable, "-m", "pip", "install", "pyinstaller", *requirements],
        check=True,
    )
    subprocess.run(
        [sys.executable, "-m", "PyInstaller", "--noconfirm", "--clean", str(_SPEC)],
        check=True,
        cwd=_HERE.parent,
    )
    print("\nBuilt dist/pytex")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
