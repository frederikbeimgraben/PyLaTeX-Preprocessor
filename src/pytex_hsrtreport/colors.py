from typing import Final

from pytex.commands.colors import Definecolor
from pytex.interface.tex import TeX
from pytex.model.concat import Concat
from pytex.registry import Registry

__all__ = ["HSRTColors"]

HSRT_PALETTE: Final[dict[str, tuple[float, float, float]]] = {
    "britishracinggreen": (0.0, 0.26, 0.15),
    "eggplant": (0.38, 0.25, 0.32),
    "hanblue": (0.27, 0.42, 0.81),
    "navyblue": (0.0, 0.0, 0.5),
    "pansypurple": (0.47, 0.09, 0.29),
    "shockingpink": (0.99, 0.06, 0.75),
    "lightgray": (0.80, 0.80, 0.80),
}


def _spec(rgb: tuple[float, float, float]) -> str:
    return f"{rgb[0]},{rgb[1]},{rgb[2]}"


@Registry.add
def HSRTColors() -> TeX:
    """Definecolor commands for all HSRT palette colors. Emit once in preamble."""
    return Concat(
        *(Definecolor(name, "rgb", _spec(rgb)) for name, rgb in HSRT_PALETTE.items())
    )
