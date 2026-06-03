"""Inline ``{{shortcode}}`` expansion for protocol Markdown.

Shortcodes are the inline counterpart to the block callouts: small widgets
(``{{time 18:30}}``, ``{{vote ja=12 nein=3 enthaltung=2}}``) and references to
frontmatter fields (``{{anwesend}}``, ``{{count anwesend}}``, ``{{datum}}``).

Unknown shortcodes are rendered back verbatim (escaped) so a typo is visible
in the PDF rather than silently dropped.
"""

from __future__ import annotations

import re
from typing import TYPE_CHECKING, Final

from pytex.commands.builtin import Textbf
from pytex.commands.colors import Textcolor
from pytex.helpers.sanitize import escape_latex
from pytex.model.concat import Concat
from pytex.model.raw import Raw

from .entries import Timestamp

if TYPE_CHECKING:
    from collections.abc import Mapping

    from pytex.interface.tex import TeX

    from ..frontmatter import FrontmatterValue

__all__ = ["SHORTCODE_RE", "expand_inline_shortcodes", "expand_shortcode"]

SHORTCODE_RE: Final[re.Pattern[str]] = re.compile(r"\{\{\s*(.*?)\s*\}\}")

# Frontmatter keys that can be referenced inline by their bare name.
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
    summary = f"Ja {yes} · Nein {no} · Enthaltung {abstain}"
    return Concat(Textbf("Abstimmung: "), Textcolor(color, summary))


def _parse_kwargs(rest: str) -> dict[str, str]:
    return dict(token.split("=", 1) for token in rest.split() if "=" in token)


def expand_shortcode(inner: str, meta: Mapping[str, FrontmatterValue]) -> TeX:
    """Expand a single ``{{...}}`` body (without braces) to a TeX node."""
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
    """Split `text` on ``{{...}}`` markers, escaping prose and expanding codes."""
    parts: list[TeX] = []
    pos = 0
    for match in SHORTCODE_RE.finditer(text):
        if match.start() > pos:
            parts.append(Raw(escape_latex(text[pos : match.start()])))
        parts.append(expand_shortcode(match.group(1), meta))
        pos = match.end()
    if pos < len(text):
        parts.append(Raw(escape_latex(text[pos:])))
    return Concat(*parts)
