"""Build the standalone `pytex` binary with PyInstaller.

    python packaging/build.py

This script installs PyInstaller and the `requirements` from `bundle.toml`
into the active environment. It then freezes the binary into `dist/pytex`.

The script changes the active environment, so run it in a new virtualenv.
You must install `pytex` first, for example with `pip install -e .`.
"""

from __future__ import annotations

import subprocess
import sys
import tomllib
from pathlib import Path

_HERE = Path(__file__).resolve().parent
_SPEC = _HERE / "pytex.spec"


def main() -> int:
    """Install the bundle requirements, then freeze the `pytex` binary.

    Returns:
        Always 0.

    Raises:
        subprocess.CalledProcessError: A pip step or a PyInstaller step exits
            with a non-zero status.
    """
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
