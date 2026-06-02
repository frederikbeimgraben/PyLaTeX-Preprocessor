# PyInstaller spec for the standalone `pytex` binary.  (Run via packaging/build.py
# or `pyinstaller packaging/pytex.spec`.)
#
# Bundles the pytex packages (with their data: HSRT fonts/logos/tex, etc.), the
# distribution metadata (so `pytex --version` works frozen), and every extra
# package listed in bundle.toml (so documents can import numpy/pandas/… at
# runtime).

import tomllib
from pathlib import Path

from PyInstaller.utils.hooks import collect_all, copy_metadata

_HERE = Path(SPECPATH)  # noqa: F821 - injected by PyInstaller

# pytex's own packages: collect_all grabs their package-data (assets/tex).
_PYTEX_PACKAGES = [
    "pytex",
    "pytex_analyze",
    "pytex_builder",
    "pytex_hsrtreport",
    "pytex_koma",
    "pytex_markdown",
    "pytex_protocol",
    "pytex_tikz",
]

_bundle = tomllib.loads((_HERE / "bundle.toml").read_text())
_extra_modules = _bundle["bundle"]["collect"]

datas = copy_metadata("pytex-preprocessor")
binaries = []
hiddenimports = []

for _name in (*_PYTEX_PACKAGES, *_extra_modules):
    _d, _b, _h = collect_all(_name)
    datas += _d
    binaries += _b
    hiddenimports += _h

a = Analysis(  # noqa: F821
    [str(_HERE / "entry.py")],
    pathex=[str(_HERE.parent / "src")],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    noarchive=False,
)
pyz = PYZ(a.pure)  # noqa: F821

exe = EXE(  # noqa: F821
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name="pytex",
    console=True,
    strip=False,
    upx=False,
)
