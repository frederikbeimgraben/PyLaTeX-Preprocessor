"""Font configuration — Python decides which fontspec branch to emit.

The original ``Config/Fonts.tex`` walked through a long ``\\IfFileExists`` /
``\\IfFontExistsTF`` ladder. Here all those file checks happen in Python at
build time: we look for the bundled ``Blender`` and ``DIN`` ttf files and emit
exactly the ``\\newfontfamily`` / ``\\setsansfont`` / ``\\setmainfont`` calls
that apply, with absolute paths baked in. No ``.tex`` file required.
"""

from dataclasses import dataclass
from typing import override

from pytex import BuiltinPackages, Package, RenewCommand, TeX
from pytex.model.raw import Raw
from pytex_komascript.model import Block

from .paths import FontsPath

_BLENDER_PATH = FontsPath / "Blender"
_BLENDER_REGULAR = _BLENDER_PATH / "Blender-Medium.ttf"
_DIN_PATH = FontsPath / "DIN"
_DIN_REGULAR = _DIN_PATH / "DIN-Regular.ttf"


@dataclass
class NewFontFamily(TeX):
    """``\\newfontfamily\\name[opts]{family}`` from ``fontspec``."""

    name: str
    family: str
    options: str | None = None

    @property
    @override
    def required_packages(self) -> set[Package | str]:
        return {BuiltinPackages.FONTSPEC.value}

    @property
    @override
    def children(self) -> tuple[TeX, ...]:
        return ()

    @override
    def serialize(self) -> str:
        opt = f"[{self.options}]" if self.options is not None else ""
        return f"\\newfontfamily\\{self.name}{opt}{{{self.family}}}"


@dataclass
class SetMainFont(TeX):
    """``\\setmainfont[opts]{family}`` from ``fontspec``."""

    family: str
    options: str | None = None

    @property
    @override
    def required_packages(self) -> set[Package | str]:
        return {BuiltinPackages.FONTSPEC.value}

    @property
    @override
    def children(self) -> tuple[TeX, ...]:
        return ()

    @override
    def serialize(self) -> str:
        opt = f"[{self.options}]" if self.options is not None else ""
        return f"\\setmainfont{opt}{{{self.family}}}"


@dataclass
class SetSansFont(TeX):
    """``\\setsansfont[opts]{family}`` from ``fontspec``."""

    family: str
    options: str | None = None

    @property
    @override
    def required_packages(self) -> set[Package | str]:
        return {BuiltinPackages.FONTSPEC.value}

    @property
    @override
    def children(self) -> tuple[TeX, ...]:
        return ()

    @override
    def serialize(self) -> str:
        opt = f"[{self.options}]" if self.options is not None else ""
        return f"\\setsansfont{opt}{{{self.family}}}"


def _font_options(directory: str, regular: str, bold: str, italic: str, bolditalic: str) -> str:
    return (
        f"Path={directory}/, Extension=.ttf,"
        f"UprightFont=*-{regular}, BoldFont=*-{bold},"
        f"ItalicFont=*-{italic}, BoldItalicFont=*-{bolditalic}"
    )


_BLENDER_OPTS = _font_options(
    directory=str(_BLENDER_PATH),
    regular="Medium",
    bold="Bold",
    italic="MediumItalic",
    bolditalic="BoldItalic",
)
_DIN_OPTS = _font_options(
    directory=str(_DIN_PATH),
    regular="Regular",
    bold="Bold",
    italic="Italic",
    bolditalic="BoldItalic",
)


def fonts_block() -> TeX:
    """Build the fontspec preamble. File presence is checked in Python.

    Always emits ``\\renewcommand*{\\rmdefault}{lmr}`` etc. so the lmodern
    fallback is wired regardless. When the Blender or DIN ttf files are
    bundled with the package we emit the corresponding ``\\newfontfamily`` and
    ``\\setsansfont`` / ``\\setmainfont`` calls with absolute paths.
    """
    parts: list[TeX] = [
        RenewCommand("rmdefault", "lmr"),
        RenewCommand("sfdefault", "lmss"),
    ]

    if _BLENDER_REGULAR.exists():
        parts.append(NewFontFamily("BlenderFont", "Blender", _BLENDER_OPTS))
        parts.append(RenewCommand("blenderfont", "\\BlenderFont"))
        parts.append(SetSansFont("Blender", _BLENDER_OPTS))
    else:
        parts.append(
            Raw(
                "\\IfFontExistsTF{Blender}"
                "{\\newfontfamily\\BlenderFont{Blender}"
                "\\renewcommand{\\blenderfont}{\\BlenderFont}\\setsansfont{Blender}}"
                "{\\newfontfamily\\BlenderFont{TeX Gyre Heros}"
                "\\renewcommand{\\blenderfont}{\\BlenderFont}"
                "\\setsansfont{TeX Gyre Heros}}",
                escape_spaces=False,
            )
        )

    if _DIN_REGULAR.exists():
        parts.append(NewFontFamily("DINFont", "DIN", _DIN_OPTS))
        parts.append(RenewCommand("dinfont", "\\DINFont"))
        parts.append(SetMainFont("DIN", _DIN_OPTS))
    else:
        parts.append(
            Raw(
                "\\IfFontExistsTF{DIN}"
                "{\\newfontfamily\\DINFont{DIN}"
                "\\renewcommand{\\dinfont}{\\DINFont}\\setmainfont{DIN}}"
                "{\\newfontfamily\\DINFont{TeX Gyre Termes}"
                "\\renewcommand{\\dinfont}{\\DINFont}"
                "\\setmainfont{TeX Gyre Termes}}",
                escape_spaces=False,
            )
        )

    return Block(*parts)


__all__ = [
    "NewFontFamily",
    "SetMainFont",
    "SetSansFont",
    "fonts_block",
]
