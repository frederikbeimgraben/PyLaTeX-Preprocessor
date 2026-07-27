"""Inline `{{shortcode}}` expansion for protocol Markdown.

A shortcode is the inline counterpart of a block callout. A shortcode builds a
small component, for example `{{time 18:30}}` or
`{{vote ja=12 nein=3 enthaltung=2}}`. A shortcode can also reference a
frontmatter field, for example `{{anwesend}}`, `{{count anwesend}}` or
`{{datum}}`.

An unknown shortcode goes back into the text as escaped literal text. You then
see the typo in the PDF. PyTeX never drops it in silence.
"""

from __future__ import annotations

import re
from typing import TYPE_CHECKING, Final

from pytex.commands.builtin import Textbf
from pytex.commands.colors import Textcolor
from pytex.helpers.sanitize import escape_latex
from pytex.model.concat import Concat
from pytex.model.raw import Raw

from ..glyphs import glyph_node
from .entries import Timestamp

if TYPE_CHECKING:
    from collections.abc import Mapping

    from pytex.interface.tex import TeX

    from ..frontmatter import FrontmatterValue

__all__ = ["SHORTCODE_RE", "expand_inline_shortcodes", "expand_shortcode"]

SHORTCODE_RE: Final[re.Pattern[str]] = re.compile(r"\{\{\s*(.*?)\s*\}\}")

# The frontmatter keys that a shortcode may reference by their bare name.
_FIELD_ALIASES: Final[dict[str, tuple[str, ...]]] = {
    "gremium": ("gremium",),
    "datum": ("datum", "date"),
    "beginn": ("beginn", "start"),
    "ende": ("ende", "end"),
    "ort": ("ort",),
    "sitzungsleitung": ("sitzungsleitung",),
    "protokoll": ("protokoll",),
    "anwesend": ("anwesend",),
    "abwesend": ("abwesend",),
    "entschuldigt": ("entschuldigt",),
    "gaeste": ("gaeste", "gäste"),
}
_LIST_FIELDS: Final[frozenset[str]] = frozenset(
    {"anwesend", "abwesend", "entschuldigt", "gaeste"}
)


def _as_list(value: FrontmatterValue | None) -> list[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    return [v.strip() for v in value.split(",") if v.strip()]


def _lookup(
    meta: Mapping[str, FrontmatterValue], field: str
) -> FrontmatterValue | None:
    for key in _FIELD_ALIASES.get(field, (field,)):
        if key in meta:
            return meta[key]
    return None


def _verbatim(inner: str) -> TeX:
    return Raw(escape_latex(f"{{{{{inner}}}}}"))


def _vote(args: dict[str, str]) -> TeX:
    def count(*keys: str) -> int:
        for key in keys:
            if key in args:
                try:
                    return int(args[key])
                except ValueError:
                    return 0
        return 0

    yes, no, abstain = (
        count("ja", "yes"),
        count("nein", "no"),
        count("enthaltung", "enth", "abstain"),
    )
    color = "britishracinggreen" if yes > no else "red" if yes < no else "eggplant"
    # `·` (U+00B7) has no glyph in the bundled DIN font. `glyph_node` rewrites
    # it to `\cdot`, so the separator needs a node here instead of a bare str.
    # `Textcolor` writes a str value verbatim and would skip that rewrite.
    summary = Concat(
        Raw(f"Ja {yes} "),
        glyph_node("·"),
        Raw(f" Nein {no} "),
        glyph_node("·"),
        Raw(f" Enthaltung {abstain}"),
    )
    return Concat(Textbf("Abstimmung: "), Textcolor(color, summary))


def _parse_kwargs(rest: str) -> dict[str, str]:
    return dict(token.split("=", 1) for token in rest.split() if "=" in token)


def expand_shortcode(inner: str, meta: Mapping[str, FrontmatterValue]) -> TeX:
    """Expand the body of one `{{...}}` marker, without the braces, to a node."""
    name, _, rest = inner.strip().partition(" ")
    name = name.lower()
    rest = rest.strip()

    if name == "time" and rest:
        return Timestamp(rest)
    if name == "vote":
        return _vote(_parse_kwargs(rest))
    if name == "count":
        return Raw(str(len(_as_list(_lookup(meta, rest.lower())))))
    if name in _FIELD_ALIASES:
        value = _lookup(meta, name)
        if name in _LIST_FIELDS:
            return Raw(escape_latex(", ".join(_as_list(value))))
        return Raw(escape_latex(value if isinstance(value, str) else ""))
    return _verbatim(inner)


def expand_inline_shortcodes(text: str, meta: Mapping[str, FrontmatterValue]) -> TeX:
    """Split `text` on the `{{...}}` markers, then escape and expand.

    `re.split` on the capturing group alternates prose and shortcode body. The
    odd pieces are the shortcode bodies. The even pieces are the prose between
    them. The function drops the empty prose pieces that two adjacent markers
    or a marker at an edge produce.
    """
    return Concat(
        *(
            expand_shortcode(piece, meta) if index % 2 else Raw(escape_latex(piece))
            for index, piece in enumerate(SHORTCODE_RE.split(text))
            if index % 2 or piece
        )
    )
