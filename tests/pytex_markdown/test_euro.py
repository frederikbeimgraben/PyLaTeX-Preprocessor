from __future__ import annotations

from typing import TYPE_CHECKING

from pytex_markdown import Markdown

if TYPE_CHECKING:
    from pytex.interface.package import PackageProtocol
    from pytex.interface.tex import TeX


def _requirements(node: TeX) -> set[str]:
    """Collect package names required anywhere in a ``TeX`` tree."""
    names: set[PackageProtocol] = set()
    stack: list[TeX] = [node]
    while stack:
        current = stack.pop()
        names.update(current.requires or ())
        stack.extend(current.children)
    return {pkg.name for pkg in names}


def test_euro_becomes_eurosym_command():
    # The DIN font has no euro glyph, so the raw char must become \euro{}.
    out = Markdown("It costs 50€.").rendered
    assert r"\euro{}" in out
    assert "€" not in out


def test_euro_registers_eurosym_package():
    tex = Markdown("Pay 5€ now.")
    assert "eurosym" in _requirements(tex)


def test_euro_preserves_surrounding_spacing():
    # `€` glued to an amount stays glued; a spaced `€` keeps its space.
    glued = Markdown("50€").rendered
    assert r"50\euro{}" in glued
    spaced = Markdown("€ 50").rendered
    assert r"\euro{} 50" in spaced


def test_multiple_euros():
    out = Markdown("From €5 to 10€ range.").rendered
    assert out.count(r"\euro{}") == 2
    assert "€" not in out


def test_euro_left_alone_in_code_span():
    # Code spans render verbatim; the euro is not rewritten there.
    out = Markdown("`50€`").rendered
    assert r"\euro{}" not in out


def test_double_quote_escaped_in_prose():
    # babel ngerman would otherwise treat the literal `"` as a shorthand.
    out = Markdown('He said "yes".').rendered
    assert r"\textquotedbl{}" in out
    assert '"' not in out
