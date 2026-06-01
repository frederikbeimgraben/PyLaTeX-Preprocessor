from collections.abc import Iterator
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

LOGO_DIR: Final[Path] = Path(str(files("pytex_hsrtreport").joinpath("assets/logos")))


KNOWN_LOGOS: Final[dict[str, str]] = {
    "HSRT": "HSRT.pdf",
    "INF": "INF.pdf",
    "ASTA": "ASTA.svg",
    "STUPA": "STUPA.pdf",
    "ECHO": "ECHO.svg",
    "Skyline": "Skyline.pdf",
}


def logo_path(name: str) -> Path:
    if name not in KNOWN_LOGOS:
        raise ValueError(f"unknown HSRT logo {name!r}; known: {sorted(KNOWN_LOGOS)}")
    return LOGO_DIR / KNOWN_LOGOS[name]


# Output dir for logos referenced by the tikz overlays, relative to the .tex
# file. `HSRTReport.write_inline_logos` copies the (svg->pdf converted) files
# here. The overlays emit these relative paths instead of absolute source
# paths so tectonic can read them (absolute paths outside the build cwd trip
# tectonic's "non-reproducible" warning and forbid reading the .bb bbox file).
LOGO_OUTPUT_DIR: Final[str] = "logos"


def logo_output_name(name: str) -> str:
    """Filename of a logo as materialised in the output ``logos/`` dir.

    SVG sources are converted to PDF, so they get a ``.pdf`` suffix.
    """
    src = logo_path(name)
    if src.suffix.lower() == ".svg":
        return f"{src.stem}.pdf"
    return src.name


def logo_output_rel(name: str) -> str:
    """Path of a logo relative to the .tex file (e.g. ``logos/INF.pdf``)."""
    return f"{LOGO_OUTPUT_DIR}/{logo_output_name(name)}"


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
    logos = (
        Logo(name, scale=scale, height=height, inline_base64=inline_base64)
        for name in names
    )
    sep = _sep(separator)
    # Interleave a separator before every logo except the first.
    return Concat(
        *(
            piece
            for i, logo in enumerate(logos)
            for piece in ((sep, logo) if i else (logo,))
        )
    )


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


def titlepage_logo_overlay(
    names: tuple[str, ...],
    logo_height: str = "1.4cm",
    xshift: str = "1.5cm",
    yshift: str = "-1.5cm",
    node_sep: str = "0.5cm",
    prefix: str = "tplogo",
) -> str:
    """Raw LaTeX: tikz overlay placing logos at the top-left of the page.

    Mirrors the ``\\foreach`` loop in ``tmp/Pages/Titlepage.tex`` but
    unrolled in Python so no LaTeX arrays or counters are needed.
    """
    if not names:
        return ""

    def lines() -> Iterator[str]:
        yield r"\begin{tikzpicture}[overlay, remember picture]"
        # Invisible dummy anchor at the top-left page corner — the chain
        # start (logo0), mirroring the DUMMY_FOOT node in the original.
        yield (
            "  \\node[anchor=north west, inner sep=0pt, "
            + f"xshift={xshift}, yshift={yshift}, opacity=0] ({prefix}0) "
            + f"at (current page.north west) {{\\rule{{0pt}}{{{logo_height}}}}};"
        )
        for i, name in enumerate(names, 1):
            path = logo_output_rel(name)
            yield (
                f"  \\node[anchor=west, inner sep=0pt, xshift={node_sep}] "
                + f"({prefix}{i}) at ({prefix}{i - 1}.east) "
                + f"{{\\includegraphics[height={logo_height}]{{{path}}}}};"
            )
        yield r"\end{tikzpicture}"

    return "\n".join(lines())


def footer_logo_hook(
    names: tuple[str, ...],
    logo_height: str = "0.8cm",
    xshift: str = "-2cm",
    yshift: str = "1.5em",
    node_sep: str = "-0.3cm",
    prefix: str = "fllogo",
    skyline: bool = True,
) -> str:
    """Raw LaTeX: ``\\AddToHook{shipout/background}`` block placing logos at
    the bottom-right of every page.

    Mirrors the ``\\foreach`` loop in ``tmp/Modules/Layout/Logos.tex`` but
    unrolled in Python.  Logos are chained right-to-left from a dummy anchor
    at the page's south-east corner.  The skyline graphic is placed at the
    south-west corner when ``skyline=True`` (matching the original template).

    The footer logos are wrapped in ``\\ifHSRTTitlePage\\else...\\fi`` so they
    are suppressed on the title page (which sets ``\\HSRTTitlePagetrue``); the
    skyline graphic is unconditional.
    """
    if not names and not skyline:
        return ""

    def lines() -> Iterator[str]:
        yield r"\AddToHook{shipout/background}{%"
        yield r"  \begin{tikzpicture}[overlay, remember picture]"
        if names:
            # Suppress footer logos on the title page.
            yield r"  \ifHSRTTitlePage\else"
            # Invisible dummy anchor at the bottom-right page corner.
            yield (
                "  \\node[anchor=south east, inner sep=0pt, "
                + f"xshift={xshift}, yshift={yshift}, opacity=0] ({prefix}0) "
                + f"at (current page.south east) {{\\rule{{0pt}}{{{logo_height}}}}};"
            )
            # Chain logos from right to left (anchor=east, stepping west).
            for i, name in enumerate(names, 1):
                path = logo_output_rel(name)
                yield (
                    "  \\node[anchor=east, inner sep=0pt, "
                    + f"xshift={node_sep}, yshift=2pt] ({prefix}{i}) "
                    + f"at ({prefix}{i - 1}.west) "
                    + f"{{\\includegraphics[height={logo_height}]{{{path}}}}};"
                )
            yield r"  \fi"
        if skyline:
            skyline_path = logo_output_rel("Skyline")
            yield (
                "  \\node[anchor=south west, inner sep=0pt, yshift=0em] "
                + "at (current page.south west) "
                + f"{{\\includegraphics[width=1.5\\paperwidth]{{{skyline_path}}}}};"
            )
        yield r"  \end{tikzpicture}%"
        yield r"}"

    return "\n".join(lines())


# Keep SelectColor import alive for callers that previously imported via this module
__all__ = [
    "LOGO_OUTPUT_DIR",
    "DefaultLogos",
    "Includegraphics",
    "Logo",
    "LogoStrip",
    "SelectColor",
    "footer_logo_hook",
    "logo_output_name",
    "logo_output_rel",
    "logo_path",
    "titlepage_logo_overlay",
]
