"""Per-page footer logo overlay — built declaratively with :mod:`pytex_tikz`.

The original .cls stored logos in arrayjobx and walked them with ``\\foreach``
inside ``\\AtBeginPage``. After the refactor everything lives in Python: the
resolved ``(name, scale)`` list is iterated at build time and the tikz overlay
is composed of native :class:`pytex_tikz.Node` instances with absolute logo
paths baked in. No ``\\logosScale`` / ``\\imageHeight`` TeX-side state.
"""

from pytex import Command, TeX
from pytex.library import IncludeGraphics
from pytex_tikz import Coordinate, Node, TikzPicture

from .paths import DummyFootPath, SkylinePath, logo_pdf
from .variants import resolve_logos

#: Default global scale (the .cls used \logosScale=1).
DEFAULT_GLOBAL_SCALE: float = 1.0
#: Default main-logo scale (the .cls used \mainLogoScale=1).
DEFAULT_MAIN_SCALE: float = 1.0
#: Footer logo height = 1.5cm × logo_scale × global_scale × this factor.
FOOTER_SHRINK: float = 0.55
#: Dummy-foot height = 2cm × main_scale × global_scale × this factor.
DUMMY_FOOT_SHRINK: float = 0.45


def _height_cm(base_cm: float, *factors: float) -> str:
    value = base_cm
    for f in factors:
        value *= f
    return f"{value:g}cm"


def _logo_node(
    index: int,
    name: str,
    scale: float,
    global_scale: float,
) -> Node:
    """One tikz ``\\node`` for a logo in the at-begin-page footer strip."""
    height = _height_cm(1.5, scale, global_scale, FOOTER_SHRINK)
    return Node(
        IncludeGraphics(str(logo_pdf(name)), height=height),
        options="anchor=east, inner sep=0pt, xshift=-1.5cm, yshift=2pt",
        name=f"logo{index}",
        at=Coordinate.named(f"logo{index - 1}", "west"),
    )


def _dummy_foot_node(global_scale: float, main_scale: float) -> Node:
    """Invisible south-east anchor node (logo0) holding DUMMY_FOOT.png."""
    height = _height_cm(2.0, main_scale, global_scale, DUMMY_FOOT_SHRINK)
    return Node(
        IncludeGraphics(str(DummyFootPath), height=height),
        options=(
            "anchor=south east, inner sep=0pt, "
            "xshift=-\\rightmargin, yshift=1.5em, opacity=0.0"
        ),
        name="logo0",
        at=Coordinate.page("south east"),
    )


def _skyline_node() -> Node:
    """Skyline image anchored at the bottom-left of the page."""
    return Node(
        IncludeGraphics(str(SkylinePath), width="1.5\\paperwidth"),
        options="anchor=south west, inner sep=0pt, yshift=0em",
        at=Coordinate.page("south west"),
    )


def at_begin_page_block(
    resolved: list[tuple[str, float]],
    footer_logos: bool,
    *,
    global_scale: float = DEFAULT_GLOBAL_SCALE,
    main_scale: float = DEFAULT_MAIN_SCALE,
) -> TeX:
    """``\\AtBeginPage{ <tikzpicture> }`` — skyline + optional footer logos."""
    nodes: list[Node] = [_dummy_foot_node(global_scale, main_scale)]
    if footer_logos:
        nodes.extend(
            _logo_node(i, name, scale, global_scale)
            for i, (name, scale) in enumerate(resolved, start=1)
        )
    nodes.append(_skyline_node())
    pic = TikzPicture(*nodes, options="overlay, remember picture")
    return Command("AtBeginPage", pic)


def logos_block(
    variant: str,
    logos: "set[str] | list[str] | tuple[str, ...] | dict[str, float] | None",
    footer_logos: bool,
    *,
    global_scale: float = DEFAULT_GLOBAL_SCALE,
    main_scale: float = DEFAULT_MAIN_SCALE,
) -> tuple[TeX, list[tuple[str, float]]]:
    """Resolve the logo set and emit the AtBeginPage overlay.

    Returns the TeX block and the resolved list so the caller can reuse the
    same logo set for the title-page header strip.
    """
    resolved = resolve_logos(variant, logos)
    block = at_begin_page_block(
        resolved,
        footer_logos,
        global_scale=global_scale,
        main_scale=main_scale,
    )
    return block, resolved


def titlepage_logo_height(scale: float, global_scale: float) -> str:
    """Title-page logo height (``1.5cm × scale × global``)."""
    return _height_cm(1.5, scale, global_scale)


def titlepage_main_height(main_scale: float, global_scale: float) -> str:
    """Title-page hero (DUMMY_FOOT) height — ``2cm × main × global``."""
    return _height_cm(2.0, main_scale, global_scale)


# Re-exported so titlepage can compose pre-built logo nodes too.
def titlepage_logo_node(
    index: int,
    name: str,
    scale: float,
    global_scale: float,
) -> Node:
    """One ``\\node`` for the title-page header logo strip."""
    height = titlepage_logo_height(scale, global_scale)
    return Node(
        IncludeGraphics(str(logo_pdf(name)), height=height),
        options="anchor=west, inner sep=0pt, xshift=0.5cm",
        name=f"logo{index}",
        at=Coordinate.named(f"logo{index - 1}", "east"),
    )


__all__ = [
    "DEFAULT_GLOBAL_SCALE",
    "DEFAULT_MAIN_SCALE",
    "FOOTER_SHRINK",
    "DUMMY_FOOT_SHRINK",
    "at_begin_page_block",
    "logos_block",
    "titlepage_logo_height",
    "titlepage_main_height",
    "titlepage_logo_node",
]
