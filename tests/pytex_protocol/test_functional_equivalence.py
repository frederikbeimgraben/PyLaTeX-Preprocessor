"""Equivalence tests for the rewritten meeting protocol helpers.

A rewrite replaced the loops in `_join` and `_leaf_texts`
(`pytex_markdown.protocol.convert`) and in `expand_inline_shortcodes`
(`pytex_markdown.protocol.shortcodes`) with generators and comprehensions.
This file keeps a copy of each original loop version and compares the two
against the same input.
"""

from __future__ import annotations

from types import SimpleNamespace
from typing import TYPE_CHECKING

from pytex.helpers.sanitize import escape_latex
from pytex.model.concat import Concat
from pytex.model.empty import Empty
from pytex.model.raw import Raw
from pytex_markdown.protocol.convert import _join, _leaf_texts
from pytex_markdown.protocol.shortcodes import (
    SHORTCODE_RE,
    expand_inline_shortcodes,
    expand_shortcode,
)

if TYPE_CHECKING:
    from collections.abc import Mapping

    from pytex.interface.tex import TeX
    from pytex_markdown.frontmatter import FrontmatterValue


def _node(children: object) -> SimpleNamespace:
    """Make a marko-like node, which is any object with a `children` attribute."""
    return SimpleNamespace(children=children)


# -- the original loop versions, kept as the reference ----------------------


def _old_join(blocks: list[TeX]) -> list[TeX]:
    parbreak = Raw("\n\n")
    kept = [b for b in blocks if b is not Empty]
    out: list[TeX] = []
    for i, b in enumerate(kept):
        if i:
            out.append(parbreak)
        out.append(b)
    return out


def _old_leaf_texts(node: object) -> list[str]:
    children = getattr(node, "children", None)
    if isinstance(children, str):
        return [children]
    out: list[str] = []
    for child in children if isinstance(children, list) else []:
        out.extend(_old_leaf_texts(child))
    return out


def _old_expand_inline_shortcodes(
    text: str, meta: Mapping[str, FrontmatterValue]
) -> TeX:
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


# -- tests ------------------------------------------------------------------


def test_join_matches_reference():
    blocks: list[TeX] = [Raw("a"), Empty, Raw("b"), Raw("c"), Empty]
    new = Concat(*_join(blocks)).rendered
    old = Concat(*_old_join(blocks)).rendered
    assert new == old
    assert new == "a\n\nb\n\nc"


def test_leaf_texts_matches_reference():
    # A leaf is a node whose `children` is a string. The source order counts.
    tree = _node(
        [
            _node("first"),
            _node([_node("second"), _node("third")]),
            _node([_node([_node("fourth")])]),
        ]
    )
    assert _leaf_texts(tree) == _old_leaf_texts(tree)
    assert _leaf_texts(tree) == ["first", "second", "third", "fourth"]
    assert _leaf_texts(_node([])) == []


SHORTCODE_META: Mapping[str, FrontmatterValue] = {
    "gremium": "Vorstand",
    "datum": "2026-06-04",
    "anwesend": ["Alice", "Bob", "Carol"],
}

SHORTCODE_SAMPLES = [
    "",
    "no shortcodes here",
    "{{datum}}",
    "leading {{datum}} trailing",
    "{{datum}}{{gremium}}",  # adjacent shortcodes, with no prose between them
    "a{{gremium}}b",
    "count: {{count anwesend}}",
    "{{time 18:30}} start",
    "{{unknown_code}} stays verbatim",
    "escape me: 100% & _ then {{datum}}",
    "{{datum}}",  # the whole text is one shortcode, with no prose around it
]


def test_expand_inline_shortcodes_matches_reference():
    for text in SHORTCODE_SAMPLES:
        new = expand_inline_shortcodes(text, SHORTCODE_META).rendered
        old = _old_expand_inline_shortcodes(text, SHORTCODE_META).rendered
        assert new == old, text
