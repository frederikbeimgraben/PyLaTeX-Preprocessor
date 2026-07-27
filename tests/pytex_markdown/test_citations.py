from pytex.interface.tex import TeX
from pytex_markdown import Markdown


def _requirements(node: TeX) -> set[str]:
    names: set[str] = set()
    stack: list[TeX] = [node]
    while stack:
        current = stack.pop()
        names.update(p.name for p in (current.requires or ()))
        stack.extend(current.children)
    return names


def test_bracketed_citation_becomes_autocite():
    out = Markdown("See [@knuth1984].").rendered
    assert r"\autocite{knuth1984}" in out


def test_citation_registers_biblatex():
    assert "biblatex" in _requirements(Markdown("See [@knuth1984]."))


def test_citation_with_postnote():
    out = Markdown("See [@knuth1984, S. 5].").rendered
    assert r"\autocite[S. 5]{knuth1984}" in out


def test_multiple_keys_in_one_bracket():
    out = Markdown("Both [@a; @b] agree.").rendered
    assert r"\autocite{a,b}" in out


def test_narrative_citation_becomes_textcite():
    out = Markdown("As @knuth1984 shows.").rendered
    assert r"\textcite{knuth1984}" in out


def test_trailing_punctuation_not_part_of_key():
    # The converter must keep a sentence-final period out of the citation key.
    out = Markdown("As @knuth1984.").rendered
    assert r"\textcite{knuth1984}." in out


def test_internal_punctuation_kept_in_key():
    out = Markdown("See @einstein.1905 here.").rendered
    assert r"\textcite{einstein.1905}" in out


def test_non_citation_bracket_left_as_text():
    out = Markdown("Not a cite [just text].").rendered
    assert r"\autocite" not in out and r"\textcite" not in out
    assert "just text" in out


def test_citation_not_expanded_in_code_span():
    out = Markdown("`[@knuth]`").rendered
    assert r"\autocite" not in out
    assert r"\texttt{[@knuth]}" in out


def test_email_is_not_a_narrative_citation():
    out = Markdown("write to a@b.com today").rendered
    assert r"\textcite" not in out


def test_narrative_citation_key_stops_before_hash():
    # A "#" must never reach \textcite unescaped. TeX reads an unbraced "#"
    # in an argument as a macro parameter marker and aborts the compile pass.
    out = Markdown("see @smith#2 now").rendered
    assert r"\textcite{smith#2}" not in out
    assert r"\textcite{smith}" in out
    assert r"\#2" in out


def test_narrative_citation_key_stops_before_percent():
    # A "#" in an argument comments out the remainder of the TeX source line.
    out = Markdown("see @a%b now").rendered
    assert r"\textcite{a%b}" not in out
    assert r"\textcite{a}" in out
    assert r"\%b" in out
