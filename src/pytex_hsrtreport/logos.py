"""The vendored HSRT logos and the tikz overlays that place them."""

import hashlib
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
    "MAKERS": "MAKERS.svg",
    "MAKERS-RAlign": "MAKERS-RAlign.svg",
    "MAKERS-Icon": "MAKERS-Icon.svg",
    "Skyline": "Skyline.pdf",
}


def logo_path(name: str) -> Path:
    """Resolve a logo reference to a file.

    Args:
        name: A vendored logo key such as `INF` or `MAKERS`. A path to a
            custom image file also works. Such a file has a suffix such as
            `.svg`, `.pdf` or `.png`.

    Returns:
        The path of the logo file.

    Raises:
        ValueError: The name is neither a vendored logo key nor the path of
            an existing file.
    """
    if name in KNOWN_LOGOS:
        return LOGO_DIR / KNOWN_LOGOS[name]
    candidate = Path(name).expanduser()
    if candidate.is_file():
        return candidate
    raise ValueError(
        f"unknown logo {name!r}: not a vendored logo {sorted(KNOWN_LOGOS)} "
        + "nor an existing file path"
    )


# Directory for the logos that the tikz overlays use, relative to the rendered
# `.tex` file. `HSRTReport.write_inline_logos` writes the files to disk here
# and converts SVG to PDF on the way. The overlays name these relative paths,
# not the absolute source paths. The tectonic binary reports an absolute path
# outside the build directory as non-reproducible. It also refuses to read the
# `.bb` bounding-box file for such a path.
LOGO_OUTPUT_DIR: Final[str] = "logos"


def logo_output_name(name: str) -> str:
    """Return the file name that a logo gets in the `logos/` directory.

    PyTeX converts an SVG source to PDF, so an SVG logo gets the `.pdf`
    suffix. A custom (non-vendored) path also gets a short hash of its
    absolute location. Two custom logos that share a stem, or that clash with
    a vendored name, then never collide in `logos/`.
    """
    src = logo_path(name)
    suffix = ".pdf" if src.suffix.lower() == ".svg" else src.suffix
    if name in KNOWN_LOGOS:
        return f"{src.stem}{suffix}"
    digest = hashlib.sha1(str(src.resolve()).encode()).hexdigest()[:8]
    return f"{src.stem}-{digest}{suffix}"


def logo_output_rel(name: str) -> str:
    """Return the path of a logo relative to the rendered `.tex` file.

    Example:
        `logos/INF.pdf`
    """
    return f"{LOGO_OUTPUT_DIR}/{logo_output_name(name)}"


@Registry.add
def Logo(
    name: str,
    scale: float = 1.0,
    height: str | None = None,
    inline_base64: bool = True,
) -> TeX:
    """Include one logo image.

    Args:
        name: A vendored logo key or the path of a custom image file.
        scale: The scale factor. PyTeX ignores it when `height` is set.
        height: A LaTeX length such as `1.4cm`. It replaces `scale`.
        inline_base64: When true, PyTeX embeds the image as base64 in the
            rendered `.tex` file.
    """
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
    """Place the named logos in a horizontal row.

    Args:
        separator: Raw LaTeX that PyTeX puts between two logos.

    Returns:
        The `Empty` node when `names` is empty.
    """
    if not names:
        from pytex.model.empty import Empty

        return Empty
    logos = (
        Logo(name, scale=scale, height=height, inline_base64=inline_base64)
        for name in names
    )
    sep = _sep(separator)
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
    """Place the default logos of a variant in a horizontal row."""
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
    r"""Return raw LaTeX for a tikz overlay that puts logos at the top left.

    This function mirrors the `\foreach` loop in `tmp/Pages/Titlepage.tex`.
    Python unrolls the loop, so the LaTeX needs no arrays and no counters.

    Returns:
        An empty string when `names` is empty.
    """
    if not names:
        return ""

    def lines() -> Iterator[str]:
        yield r"\begin{tikzpicture}[overlay, remember picture]"
        # An invisible anchor at the top-left page corner starts the chain.
        # It mirrors the `DUMMY_FOOT` node in the original template.
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
    r"""Return raw LaTeX that puts logos at the bottom right of every page.

    The block is an `\AddToHook{shipout/background}` hook. It mirrors the
    `\foreach` loop in `tmp/Modules/Layout/Logos.tex`, unrolled in Python. The
    logos chain from right to left. The chain starts at an anchor in the
    south-east corner of the page.

    When `skyline` is true, the hook also places the skyline graphic in the
    south-west corner. This matches the original template.

    The footer logos sit inside `\ifHSRTTitlePage\else...\fi`. The title page
    sets `\HSRTTitlePagetrue`, so LaTeX leaves the footer logos out there. The
    skyline graphic has no such condition.

    Returns:
        An empty string when `names` is empty and `skyline` is false.
    """
    if not names and not skyline:
        return ""

    def lines() -> Iterator[str]:
        yield r"\AddToHook{shipout/background}{%"
        yield r"  \begin{tikzpicture}[overlay, remember picture]"
        if names:
            # Leave the footer logos out on the title page.
            yield r"  \ifHSRTTitlePage\else"
            # An invisible anchor at the bottom-right page corner starts the
            # chain.
            yield (
                "  \\node[anchor=south east, inner sep=0pt, "
                + f"xshift={xshift}, yshift={yshift}, opacity=0] ({prefix}0) "
                + f"at (current page.south east) {{\\rule{{0pt}}{{{logo_height}}}}};"
            )
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


# `SelectColor` and `Includegraphics` stay here for callers that imported them
# from this module before.
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
