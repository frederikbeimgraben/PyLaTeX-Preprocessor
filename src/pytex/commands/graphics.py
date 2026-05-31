from ..helpers.with_package import with_package
from ..interface.tex import TeX
from ..model.control_sequence import ControlSequence, Parameter
from ..model.raw import Raw
from ..packages import GRAPHICX
from ..registry import Registry


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
    opts: list[str] = []
    if width is not None:
        opts.append(f"width={width}")
    if height is not None:
        opts.append(f"height={height}")
    if scale is not None:
        opts.append(f"scale={scale}")
    if angle is not None:
        opts.append(f"angle={angle}")
    if keepaspectratio:
        opts.append("keepaspectratio")
    if extra_options:
        opts.extend(f"{k}={v}" for k, v in extra_options.items())
    params: tuple[Parameter, ...]
    if opts:
        params = (Parameter(Raw(",".join(opts)), optional=True), Parameter(path))
    else:
        params = (Parameter(path),)
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
