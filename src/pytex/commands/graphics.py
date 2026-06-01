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
    inner = "".join(f"{{{p}}}" for p in paths)
    return ControlSequence("graphicspath", (Parameter(Raw(inner)),))


@Registry.add
@with_package(GRAPHICX)
def Resizebox(width: str, height: str, body: TeX | str) -> TeX:
    return ControlSequence(
        "resizebox",
        (Parameter(width), Parameter(height), Parameter(body)),
    )


@Registry.add
@with_package(GRAPHICX)
def Scalebox(scale: str, body: TeX | str) -> TeX:
    return ControlSequence("scalebox", (Parameter(scale), Parameter(body)))


@Registry.add
@with_package(GRAPHICX)
def Rotatebox(angle: str, body: TeX | str) -> TeX:
    return ControlSequence("rotatebox", (Parameter(angle), Parameter(body)))
