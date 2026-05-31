from importlib.resources import files
from pathlib import Path
from typing import Final

from pytex.commands.colors import SelectColor
from pytex.commands.graphics import Includegraphics
from pytex.interface.tex import TeX
from pytex.model.concat import Concat
from pytex.model.image import IncludeImage
from pytex.registry import Registry

from .variants import Variant

_LOGO_DIR: Final[Path] = Path(str(files("pytex_hsrtreport").joinpath("assets/logos")))


_KNOWN_LOGOS: Final[dict[str, str]] = {
    "HSRT": "HSRT.pdf",
    "INF": "INF.pdf",
    "ASTA": "ASTA.svg",
    "STUPA": "STUPA.pdf",
    "ECHO": "ECHO.svg",
    "Skyline": "Skyline.pdf",
}


def logo_path(name: str) -> Path:
    if name not in _KNOWN_LOGOS:
        raise ValueError(
            f"unknown HSRT logo {name!r}; known: {sorted(_KNOWN_LOGOS)}"
        )
    return _LOGO_DIR / _KNOWN_LOGOS[name]


@Registry.add
def Logo(
    name: str,
    scale: float = 1.0,
    height: str | None = None,
    inline_base64: bool = True,
) -> TeX:
    """Vendored HSRT logo via `IncludeImage` (auto-bakes base64 by default)."""
    return IncludeImage(
        path=logo_path(name),
        inline_base64=inline_base64,
        scale=None if height is not None else str(scale),
        height=height,
    )


@Registry.add
def LogoStrip(
    names: tuple[str, ...],
    scale: float = 1.0,
    height: str | None = None,
    separator: str = "\\hspace{0.5cm}",
    inline_base64: bool = True,
) -> TeX:
    """Horizontal sequence of vendored logos."""
    if not names:
        from pytex.model.empty import Empty
        return Empty
    pieces: list[TeX] = []
    for i, name in enumerate(names):
        if i > 0:
            pieces.append(_sep(separator))
        pieces.append(Logo(name, scale=scale, height=height, inline_base64=inline_base64))
    return Concat(*pieces)


def _sep(text: str) -> TeX:
    from pytex.model.raw import Raw
    return Raw(text)


@Registry.add
def DefaultLogos(
    variant: Variant,
    scale: float = 1.0,
    height: str | None = None,
    inline_base64: bool = True,
) -> TeX:
    from .variants import default_logo_names
    return LogoStrip(
        default_logo_names(variant),
        scale=scale,
        height=height,
        inline_base64=inline_base64,
    )


# Keep SelectColor import alive for callers that previously imported via this module
__all__ = [
    "Logo",
    "LogoStrip",
    "DefaultLogos",
    "logo_path",
    "SelectColor",
    "Includegraphics",
]
