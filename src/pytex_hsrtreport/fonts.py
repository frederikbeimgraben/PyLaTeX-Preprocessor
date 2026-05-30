"""Font configuration — Python decides which fontspec branch to emit.

The original ``Config/Fonts.tex`` walked through a long ``\\IfFileExists`` /
``\\IfFontExistsTF`` ladder. Here all those file checks happen in Python at
build time: we look for the bundled ``Blender`` and ``DIN`` ttf files and emit
exactly the ``\\newfontfamily`` / ``\\setsansfont`` / ``\\setmainfont`` calls
that apply, with absolute paths baked in. Runtime fallbacks (``IfFontExistsTF``)
are emitted as native nodes from :mod:`pytex.library.builtins.lowlevel`.
"""

from pytex import (
    IfFontExistsTF,
    NewFontFamily,
    RenewCommand,
    SetMainFont,
    SetSansFont,
    TeX,
)
from pytex_komascript.model import Block

from .paths import FontsPath

_BLENDER_PATH = FontsPath / "Blender"
_BLENDER_REGULAR = _BLENDER_PATH / "Blender-Medium.ttf"
_DIN_PATH = FontsPath / "DIN"
_DIN_REGULAR = _DIN_PATH / "DIN-Regular.ttf"


def _font_options(
    directory: str, regular: str, bold: str, italic: str, bolditalic: str
) -> str:
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
            _font_fallback("BlenderFont", "blenderfont", "Blender", "TeX Gyre Heros", sans=True)
        )

    if _DIN_REGULAR.exists():
        parts.append(NewFontFamily("DINFont", "DIN", _DIN_OPTS))
        parts.append(RenewCommand("dinfont", "\\DINFont"))
        parts.append(SetMainFont("DIN", _DIN_OPTS))
    else:
        parts.append(
            _font_fallback("DINFont", "dinfont", "DIN", "TeX Gyre Termes", sans=False)
        )

    return Block(*parts)


def _font_branch(
    macro: str,
    switch: str,
    family: str,
    *,
    sans: bool,
) -> TeX:
    """One side of the ``\\IfFontExistsTF`` body for a fontspec family."""
    setter: TeX = SetSansFont(family) if sans else SetMainFont(family)
    return Block(
        NewFontFamily(macro, family),
        RenewCommand(switch, f"\\{macro}"),
        setter,
    )


def _font_fallback(
    macro: str,
    switch: str,
    preferred: str,
    gyre: str,
    *,
    sans: bool,
) -> TeX:
    """Runtime fallback ladder used when the bundled TTF is missing.

    Emits an ``\\IfFontExistsTF`` guard: prefer the named system font, else
    drop to a TeX Gyre alternative.
    """
    return IfFontExistsTF(
        preferred,
        _font_branch(macro, switch, preferred, sans=sans),
        _font_branch(macro, switch, gyre, sans=sans),
    )


__all__ = [
    "NewFontFamily",
    "SetMainFont",
    "SetSansFont",
    "fonts_block",
]
