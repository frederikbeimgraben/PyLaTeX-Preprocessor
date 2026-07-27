# PyInstaller spec for the standalone `pytex` binary. Run it through
# `packaging/build.py` or through `pyinstaller packaging/pytex.spec`.
#
# The spec bundles three things:
#
# 1. The pytex packages with their data, for example the HSRT fonts, logos and
#    tex files.
# 2. The distribution metadata, so `pytex --version` works in the frozen
#    binary.
# 3. Every extra package that `bundle.toml` lists, so a document can import
#    numpy or pandas at runtime.

import tomllib
from pathlib import Path

from PyInstaller.utils.hooks import collect_all, copy_metadata

_HERE = Path(SPECPATH)  # noqa: F821 - injected by PyInstaller

# `collect_all` also takes the package data of these packages, for example the
# `assets` and `tex` folders.
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
