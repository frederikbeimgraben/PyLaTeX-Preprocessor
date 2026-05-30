"""Asset-path singletons for the HSRT report layout.

Each path is a :class:`pytex.TeX` node whose ``serialize()`` returns the
absolute filesystem string. Used directly in Python builders or inlined into
``.tex`` files via the escape syntax ``\\iffalse{ pytex(FontsPath) }\\fi``.

This module is the single source of truth for asset locations — no more
``\\def\\classPath{...}`` in TeX.
"""

from dataclasses import dataclass
from pathlib import Path
from typing import override

from pytex import TeX

#: Package-installed ``Assets`` directory.
ASSETS_DIR: Path = Path(__file__).parent / "Assets"


@dataclass(frozen=True)
class AssetPath(TeX):
    """A filesystem path that serialises as its absolute string.

    Supports ``/`` to derive children, matching :class:`pathlib.Path`.
    """

    path: Path

    @property
    @override
    def children(self) -> tuple[TeX, ...]:
        return ()

    @override
    def serialize(self) -> str:
        return str(self.path)

    @override
    def __str__(self) -> str:
        return str(self.path)

    def __fspath__(self) -> str:
        return str(self.path)

    def __truediv__(self, segment: "str | Path") -> "AssetPath":
        return AssetPath(self.path / segment)

    def exists(self) -> bool:
        return self.path.exists()


#: Asset root.
ClassPath: AssetPath = AssetPath(ASSETS_DIR)
#: Fonts directory.
FontsPath: AssetPath = ClassPath / "Fonts"
#: Images directory.
ImagesPath: AssetPath = ClassPath / "Images"
#: Logos sub-directory.
LogosPath: AssetPath = ImagesPath / "Logos"
#: Skyline image (placed at the bottom of every page by the footer overlay).
SkylinePath: AssetPath = ImagesPath / "Skyline.pdf"
#: Invisible footer placeholder used as the tikz anchor for logo chains.
DummyFootPath: AssetPath = ImagesPath / "DUMMY_FOOT.png"


def logo_pdf(name: str) -> AssetPath:
    """Path to a logo PDF inside :data:`LogosPath` (``name.pdf``)."""
    return LogosPath / f"{name}.pdf"


__all__ = [
    "ASSETS_DIR",
    "AssetPath",
    "ClassPath",
    "FontsPath",
    "ImagesPath",
    "LogosPath",
    "SkylinePath",
    "DummyFootPath",
    "logo_pdf",
]
