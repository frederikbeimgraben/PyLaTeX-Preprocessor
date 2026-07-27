from __future__ import annotations

from typing import TYPE_CHECKING

from pytex_markdown import Markdown

if TYPE_CHECKING:
    from pytex.interface.package import PackageProtocol
    from pytex.interface.tex import TeX


def _requirements(node: TeX) -> set[str]:
    """Collect the names of every package requirement in a node tree."""
    names: set[PackageProtocol] = set()
    stack: list[TeX] = [node]
    while stack:
        current = stack.pop()
        names.update(current.requires or ())
        stack.extend(current.children)
    return {pkg.name for pkg in names}


def test_euro_becomes_eurosym_command():
    # The DIN font has no euro glyph, so the raw character must become
    # `\euro{}`.
    out = Markdown("It costs 50€.").rendered
    assert r"\euro{}" in out
    assert "€" not in out


def test_euro_registers_eurosym_package():
    tex = Markdown("Pay 5€ now.")
    assert "eurosym" in _requirements(tex)


def test_euro_preserves_surrounding_spacing():
    # If `€` touches an amount, no space appears between them. If `€` has a
    # space, the space stays.
    glued = Markdown("50€").rendered
    assert r"50\euro{}" in glued
    spaced = Markdown("€ 50").rendered
    assert r"\euro{} 50" in spaced


def test_multiple_euros():
    out = Markdown("From €5 to 10€ range.").rendered
    assert out.count(r"\euro{}") == 2
    assert "€" not in out


def test_euro_left_alone_in_code_span():
    # A code span renders verbatim. The converter does not rewrite the euro
    # sign inside it.
    out = Markdown("`50€`").rendered
    assert r"\euro{}" not in out


def test_double_quote_escaped_in_prose():
    # babel ngerman reads a literal `"` as the start of a shorthand, so the
    # converter escapes it.
    out = Markdown('He said "yes".').rendered
    assert r"\textquotedbl{}" in out
    assert '"' not in out
