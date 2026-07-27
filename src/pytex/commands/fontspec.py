"""Factories for the `fontspec` package."""

from ..helpers.with_package import with_package
from ..interface.tex import TeX
from ..model.control_sequence import ControlSequence, Parameter
from ..model.raw import Raw
from ..packages import FONTSPEC
from ..registry import Registry

__all__ = [
    "Newfontfamily",
    "Setfontfamilies",
    "Setmainfont",
    "Setmonofont",
    "Setsansfont",
]


def _opts_to_str(opts: dict[str, str]) -> str:
    """Join font features into one comma-separated string.

    A key whose value is an empty string gives a bare feature name.
    """
    return ",".join(k if v == "" else f"{k}={v}" for k, v in opts.items())


@Registry.add
@with_package(FONTSPEC)
def Setmainfont(font: str, options: dict[str, str] | None = None) -> TeX:
    """Render `\\setmainfont`, which sets the main (serif) font.

    Args:
        font: The font name, or the file name when `options` names a path.
        options: fontspec font features, for example `{"Numbers": "OldStyle"}`.
            A value of an empty string gives a bare feature name. If `options`
            is None, the factory renders no optional argument.
    """
    if options is None:
        return ControlSequence("setmainfont", (Parameter(font),))
    return ControlSequence(
        "setmainfont",
        (Parameter(font), Parameter(Raw(_opts_to_str(options)), optional=True)),
    )


@Registry.add
@with_package(FONTSPEC)
def Setsansfont(font: str, options: dict[str, str] | None = None) -> TeX:
    """Render `\\setsansfont`, which sets the sans-serif font.

    Args:
        options: fontspec font features. See `Setmainfont` for the format.
    """
    if options is None:
        return ControlSequence("setsansfont", (Parameter(font),))
    return ControlSequence(
        "setsansfont",
        (Parameter(font), Parameter(Raw(_opts_to_str(options)), optional=True)),
    )


@Registry.add
@with_package(FONTSPEC)
def Setmonofont(font: str, options: dict[str, str] | None = None) -> TeX:
    """Render `\\setmonofont`, which sets the monospace font.

    Args:
        options: fontspec font features. See `Setmainfont` for the format.
    """
    if options is None:
        return ControlSequence("setmonofont", (Parameter(font),))
    return ControlSequence(
        "setmonofont",
        (Parameter(font), Parameter(Raw(_opts_to_str(options)), optional=True)),
    )


@Registry.add
@with_package(FONTSPEC)
def Newfontfamily(cmd: str, font: str, options: dict[str, str] | None = None) -> TeX:
    """Render `\\newfontfamily`, which binds a font to a new macro.

    Args:
        cmd: The macro to define, with the backslash, for example `\\MyFont`.
        options: fontspec font features. See `Setmainfont` for the format.
    """
    if options is None:
        return ControlSequence(
            "newfontfamily",
            (Parameter(Raw(cmd)), Parameter(font)),
        )
    return ControlSequence(
        "newfontfamily",
        (
            Parameter(Raw(cmd)),
            Parameter(font),
            Parameter(Raw(_opts_to_str(options)), optional=True),
        ),
    )


@Registry.add
@with_package(FONTSPEC)
def Setfontfamilies(font: str) -> TeX:
    """Render `\\setfontfamilies` with the font name.

    fontspec defines `\\setfontfamily`, not this plural name. Define
    `\\setfontfamilies` in the preamble before you use this factory.
    """
    return ControlSequence("setfontfamilies", (Parameter(font),))
