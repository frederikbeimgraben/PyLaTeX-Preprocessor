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


def test_inline_dollars_become_math():
    out = Markdown(r"Die Formel $q = \frac{b}{a}$ je Position.").rendered
    assert r"$q = \frac{b}{a}$" in out
    assert r"\textbackslash" not in out


def test_inline_math_keeps_an_escape_in_the_body():
    # marko drops the backslash of `\,`. The body of a formula needs it back.
    out = Markdown(r"Es gilt $2.400\,\text{EUR}$ pro Jahr.").rendered
    assert r"$2.400\,\text{EUR}$" in out


def test_a_price_stays_prose():
    out = Markdown("Kostet $5 und $6 pro Stück.").rendered
    assert r"\$5" in out
    assert r"\$6" in out


def test_an_escaped_dollar_opens_no_formula():
    out = Markdown(r"Der Preis \$100 und \$200 bleibt Text.").rendered
    assert r"\$100" in out
    assert r"\$200" in out


def test_a_dollar_paragraph_becomes_display_math():
    out = Markdown("$$\n\\sum_{i=1}^{n} b_i \\le 42\n$$").rendered
    assert r"\[\sum_{i=1}^{n} b_i \le 42\]" in out


def test_a_one_line_dollar_paragraph_becomes_display_math():
    assert r"\[E = mc^2\]" in Markdown("$$E = mc^2$$").rendered


def test_prose_around_a_formula_keeps_its_emphasis():
    out = Markdown(r"Ein *kursives* Wort und $a^2$ danach.").rendered
    assert r"\emph{kursives}" in out
    assert "$a^2$" in out


def test_a_formula_in_a_code_span_stays_code():
    out = Markdown("Der Code `$a$` bleibt Code.").rendered
    assert r"\texttt{\$a\$}" in out


def test_math_loads_the_math_packages():
    names = _requirements(Markdown(r"Die Formel $\text{a}$."))
    assert "amsmath" in names
    assert "amsfonts" in names
