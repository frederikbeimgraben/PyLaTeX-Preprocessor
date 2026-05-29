"""Logo placement — fully baked from Python.

The original class kept its logo list in arrayjobx storage and looped over it
twice from TeX (title page + page footer). After the refactor the list is a
plain Python ``[(name, scale), ...]`` and the per-logo ``\\node`` lines are
emitted at build time, so no ``\\AddLogo`` / ``\\foreach`` machinery remains.
Every public builder returns a :class:`pytex.TeX` node.
"""

from pytex import NewCommand, NewLength, TeX
from pytex.model.raw import Raw
from pytex_komascript.model import Block

from .variants import resolve_logos


def _titlepage_logo_node_str(index: int, name: str, scale: float) -> str:
    """Raw TeX for one tikz ``\\node`` in the title-page header strip."""
    prev = index - 1
    return (
        f"      \\node[anchor=west, inner sep=0pt, xshift=0.5cm] "
        f"(logo{index}) at (logo{prev}.east) {{%\n"
        f"        \\setlength{{\\imageHeight}}"
        f"{{1.5cm*\\real{{{scale}}}*\\real{{\\logosScale}}}}%\n"
        f"        \\begin{{tikzpicture}}\\node[] "
        f"{{\\includegraphics[height=\\imageHeight]"
        f"{{\\logospath {name}.pdf}}}};\\end{{tikzpicture}}%\n"
        f"      }};"
    )


def _footer_logo_node_str(index: int, name: str, scale: float) -> str:
    """Raw TeX for one tikz ``\\node`` in the at-begin-page footer strip."""
    prev = index - 1
    return (
        f"      \\node[anchor=east, inner sep=0pt, xshift=-1.5cm, yshift=2pt] "
        f"(logo{index}) at (logo{prev}.west) {{%\n"
        f"        \\setlength{{\\imageHeight}}"
        f"{{1.5cm*\\real{{{scale}}}*\\real{{\\logosScale}}*\\real{{0.55}}}}%\n"
        f"        \\begin{{tikzpicture}}\\node[] "
        f"{{\\includegraphics[height=\\imageHeight]"
        f"{{\\logospath {name}.pdf}}}};\\end{{tikzpicture}}%\n"
        f"      }};"
    )


def titlepage_logo_nodes(resolved: list[tuple[str, float]]) -> TeX:
    """:class:`Raw` carrying all title-page logo nodes (one per line)."""
    body = "\n".join(
        _titlepage_logo_node_str(i, name, scale)
        for i, (name, scale) in enumerate(resolved, start=1)
    )
    return Raw(body, escape_spaces=False, safe=False)


def footer_logo_nodes(resolved: list[tuple[str, float]]) -> TeX:
    """:class:`Raw` carrying all footer logo nodes (one per line)."""
    body = "\n".join(
        _footer_logo_node_str(i, name, scale)
        for i, (name, scale) in enumerate(resolved, start=1)
    )
    return Raw(body, escape_spaces=False, safe=False)


def logos_setup_block() -> TeX:
    """Path / scale macros and the ``\\imageHeight`` length used by overlays."""
    return Block(
        NewCommand("logosScale", "1"),
        NewCommand("mainLogoScale", "1"),
        NewLength("imageHeight"),
        NewCommand("logospath", "\\classPath/Images/Logos/"),
        NewCommand("skylinePath", "\\classPath/Images/Skyline.pdf"),
        NewCommand("footerYShift", "1.5em"),
        NewCommand("footerXShift", "0.7em"),
    )


def at_begin_page_block(
    footer_logos: bool,
    resolved: list[tuple[str, float]],
) -> TeX:
    """``\\AtBeginPage`` tikz overlay: skyline + optional footer logos.

    The skyline image and the leading dummy node are always emitted; the per-
    logo nodes are baked in only when ``footer_logos`` is true.
    """
    foot_inner = (
        "\n".join(
            _footer_logo_node_str(i, name, scale)
            for i, (name, scale) in enumerate(resolved, start=1)
        )
        + "\n"
        if footer_logos
        else ""
    )
    # The DUMMY_FOOT node is opacity=0.0 — it exists only as a tikz anchor for
    # the chained footer logos, so we just always emit it. The original class
    # gated it with \strcompare{\thepage}{0}; an \ifnum fallback would break
    # in the frontmatter (\thepage = roman ``i``), so we drop the gate.
    body = (
        "\\AtBeginPage{%\n"
        "  \\setlength{\\imageHeight}{2cm*\\real{\\mainLogoScale}"
        "*\\real{\\logosScale}*\\real{0.45}}%\n"
        "  \\begin{tikzpicture}[overlay, remember picture]%\n"
        "    \\node[anchor=south east, inner sep=0pt, xshift=-\\rightmargin, "
        "yshift=\\footerYShift, opacity=0.0] (logo0) at "
        "(current page.south east) {%\n"
        "      \\includegraphics[height=\\imageHeight]"
        "{\\imagesPath/DUMMY_FOOT.png}%\n"
        "    };%\n"
        f"{foot_inner}"
        "    \\node[anchor=south west, inner sep=0pt, yshift=0em] at "
        "(current page.south west) {%\n"
        "      \\includegraphics[width=1.5\\paperwidth]{\\skylinePath}%\n"
        "    };%\n"
        "  \\end{tikzpicture}%\n"
        "}"
    )
    return Raw(body, escape_spaces=False, safe=False)


def logos_block(
    variant: str,
    logos: "set[str] | list[str] | tuple[str, ...] | dict[str, float] | None",
    footer_logos: bool,
) -> tuple[TeX, list[tuple[str, float]]]:
    """Return the logo-setup TeX block and the resolved ``(name, scale)`` list.

    The list is reused by :mod:`pytex_hsrtreport.titlepage` to bake title-page
    nodes.
    """
    resolved = resolve_logos(variant, logos)
    return (
        Block(
            logos_setup_block(),
            at_begin_page_block(footer_logos, resolved),
        ),
        resolved,
    )


__all__ = [
    "logos_setup_block",
    "at_begin_page_block",
    "logos_block",
    "titlepage_logo_nodes",
    "footer_logo_nodes",
]
