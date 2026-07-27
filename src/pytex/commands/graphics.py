"""Factories for the `graphicx` package."""

from ..helpers.with_package import with_package
from ..interface.tex import TeX
from ..model.control_sequence import ControlSequence, Parameter
from ..model.raw import Raw
from ..packages import GRAPHICX
from ..registry import Registry

__all__ = ["Graphicspath", "Includegraphics", "Resizebox", "Rotatebox", "Scalebox"]


@Registry.add
@with_package(GRAPHICX)
def Includegraphics(
    path: str,
    width: str | None = None,
    height: str | None = None,
    scale: str | None = None,
    angle: str | None = None,
    keepaspectratio: bool = False,
    extra_options: dict[str, str] | None = None,
) -> TeX:
    """Render `\\includegraphics` for an image file.

    The factory drops each option that is None. If no option is left, it
    renders the macro without the optional argument.

    Args:
        width: The target width as a LaTeX length, for example
            `0.8\\textwidth`.
        height: The target height as a LaTeX length.
        scale: The scale factor as a decimal number, for example `0.5`.
        angle: The rotation angle in degrees, counterclockwise.
        keepaspectratio: If True, the image keeps its aspect ratio inside
            `width` and `height`.
        extra_options: More `key=value` options for `graphicx`, for example
            `{"trim": "0 0 0 10", "clip": "true"}`. The factory always writes
            `key=value`, so it cannot write a bare flag name.
    """
    sized = (
        f"{key}={value}"
        for key, value in (
            ("width", width),
            ("height", height),
            ("scale", scale),
            ("angle", angle),
        )
        if value is not None
    )
    flags = ("keepaspectratio",) if keepaspectratio else ()
    extra = (f"{k}={v}" for k, v in (extra_options or {}).items())
    opts = [*sized, *flags, *extra]
    params = (
        (Parameter(Raw(",".join(opts)), optional=True), Parameter(path))
        if opts
        else (Parameter(path),)
    )
    return ControlSequence("includegraphics", params)


@Registry.add
@with_package(GRAPHICX)
def Graphicspath(*paths: str) -> TeX:
    """Render `\\graphicspath`, which names the folders that hold the images.

    Args:
        paths: The folder paths. The factory wraps each path in braces. End
            each path with a slash, because LaTeX joins it to the file name
            without a separator.
    """
    inner = "".join(f"{{{p}}}" for p in paths)
    return ControlSequence("graphicspath", (Parameter(Raw(inner)),))


@Registry.add
@with_package(GRAPHICX)
def Resizebox(width: str, height: str, body: TeX | str) -> TeX:
    """Render `\\resizebox`, which scales the body to a width and a height.

    Args:
        width: The target width, or `!` to take the scale of the height.
        height: The target height, or `!` to take the scale of the width.
    """
    return ControlSequence(
        "resizebox",
        (Parameter(width), Parameter(height), Parameter(body)),
    )


@Registry.add
@with_package(GRAPHICX)
def Scalebox(scale: str, body: TeX | str) -> TeX:
    """Render `\\scalebox`, which scales the body by a factor."""
    return ControlSequence("scalebox", (Parameter(scale), Parameter(body)))


@Registry.add
@with_package(GRAPHICX)
def Rotatebox(angle: str, body: TeX | str) -> TeX:
    """Render `\\rotatebox`, which turns the body.

    Args:
        angle: The rotation angle in degrees, counterclockwise.
    """
    return ControlSequence("rotatebox", (Parameter(angle), Parameter(body)))
