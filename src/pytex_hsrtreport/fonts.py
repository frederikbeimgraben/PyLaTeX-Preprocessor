"""Font configuration — Python decides which fontspec branch to emit.

The original ``Config/Fonts.tex`` walked through a long ``\\IfFileExists`` /
``\\IfFontExistsTF`` ladder. Here all those file checks happen in Python at
build time: we look for the bundled ``Blender`` and ``DIN`` ttf files and emit
exactly the ``\\newfontfamily`` / ``\\setsansfont`` / ``\\setmainfont`` calls
that apply, with absolute paths baked in. Runtime fallbacks are emitted as
native :class:`IfFontExistsTF` nodes.
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


def _FontOptions(
    directory: str, regular: str, bold: str, italic: str, bolditalic: str
) -> str:
    return (
        f"Path={directory}/, Extension=.ttf,"
        f"UprightFont=*-{regular}, BoldFont=*-{bold},"
        f"ItalicFont=*-{italic}, BoldItalicFont=*-{bolditalic}"
    )


_BLENDER_OPTS = _FontOptions(
    directory=str(_BLENDER_PATH),
    regular="Medium",
    bold="Bold",
    italic="MediumItalic",
    bolditalic="BoldItalic",
)
_DIN_OPTS = _FontOptions(
    directory=str(_DIN_PATH),
    regular="Regular",
    bold="Bold",
    italic="Italic",
    bolditalic="BoldItalic",
)


def _BundledFontBlock(
    macro: str, switch: str, family: str, opts: str, *, sans: bool
) -> TeX:
    setter: TeX = SetSansFont(family, opts) if sans else SetMainFont(family, opts)
    return Block(
        NewFontFamily(macro, family, opts),
        RenewCommand(switch, f"\\{macro}"),
        setter,
    )


def _FontBranch(macro: str, switch: str, family: str, *, sans: bool) -> TeX:
    """One side of the ``\\IfFontExistsTF`` body for a fontspec family."""
    setter: TeX = SetSansFont(family) if sans else SetMainFont(family)
    return Block(
        NewFontFamily(macro, family),
        RenewCommand(switch, f"\\{macro}"),
        setter,
    )


def _FontFallback(
    macro: str, switch: str, preferred: str, gyre: str, *, sans: bool
) -> TeX:
    """Runtime ladder when the bundled TTF is missing: prefer named system
    font, fall back to a TeX Gyre alternative."""
    return IfFontExistsTF(
        preferred,
        _FontBranch(macro, switch, preferred, sans=sans),
        _FontBranch(macro, switch, gyre, sans=sans),
    )


def _BlenderFont() -> TeX:
    if _BLENDER_REGULAR.exists():
        return _BundledFontBlock(
            "BlenderFont", "blenderfont", "Blender", _BLENDER_OPTS, sans=True
        )
    return _FontFallback(
        "BlenderFont", "blenderfont", "Blender", "TeX Gyre Heros", sans=True
    )


def _DinFont() -> TeX:
    if _DIN_REGULAR.exists():
        return _BundledFontBlock(
            "DINFont", "dinfont", "DIN", _DIN_OPTS, sans=False
        )
    return _FontFallback(
        "DINFont", "dinfont", "DIN", "TeX Gyre Termes", sans=False
    )


def FontsBlock() -> TeX:
    """fontspec preamble with file presence checked in Python.

    Always renews ``\\rmdefault`` / ``\\sfdefault`` to lmodern so the
    fallback is wired regardless. Bundled TTFs get ``\\newfontfamily`` with
    absolute paths; otherwise a runtime :class:`IfFontExistsTF` ladder picks
    a system font or a TeX Gyre alternative.
    """
    return Block(
        RenewCommand("rmdefault", "lmr"),
        RenewCommand("sfdefault", "lmss"),
        _BlenderFont(),
        _DinFont(),
    )


__all__ = ["FontsBlock"]
