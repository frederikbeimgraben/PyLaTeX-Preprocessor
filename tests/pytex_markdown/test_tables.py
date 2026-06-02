from pytex.model.document import Document
from pytex_markdown import Markdown

TABLE = """\
| Name | Age | City |
|:-----|:---:|-----:|
| Bob  | 30  | NYC  |
| Ann  | 25  | LA   |
"""


def test_table_becomes_tabularx_with_wrapping_alignment_spec():
    out = Markdown(TABLE).rendered
    # tabularx at \linewidth with X columns so content wraps instead of
    # overflowing the page; alignment encoded via >{...} prefixes.
    spec = (
        r">{\raggedright\arraybackslash}X"
        r">{\centering\arraybackslash}X"
        r">{\raggedleft\arraybackslash}X"
    )
    assert r"\begin{tabularx}{\linewidth}{" + spec + "}" in out
    assert r"\end{tabularx}" in out


def test_table_uses_booktabs_rules():
    out = Markdown(TABLE).rendered
    assert r"\toprule" in out
    assert r"\midrule" in out
    assert r"\bottomrule" in out


def test_table_cells_joined_and_rows_terminated():
    out = Markdown(TABLE).rendered
    assert r"Name & Age & City \\" in out
    assert r"Bob & 30 & NYC \\" in out


def test_table_cell_inline_formatting_preserved():
    out = Markdown("| A |\n|---|\n| *x* |\n").rendered
    assert r"\emph{x}" in out


def test_table_pulls_in_booktabs_and_tabularx_packages():
    doc = Document(Markdown(TABLE), document_class="article")
    names = {p.name for p in doc.packages}
    assert {"booktabs", "tabularx"} <= names


def test_image_becomes_includegraphics_with_absolute_path():
    # Local image paths are made absolute so \includegraphics resolves them
    # from the build directory (the .tex is compiled there, not next to the md).
    from pathlib import Path

    out = Markdown("![alt](pics/foo.png)").rendered
    assert rf"\includegraphics{{{Path('pics/foo.png').resolve().as_posix()}}}" in out


CODE = """\
```python
def f():
    return "a very long line that would otherwise overflow the page margin"
```
"""


def test_code_block_uses_lstlisting_with_breaklines():
    out = Markdown(CODE).rendered
    assert r"\begin{lstlisting}[breaklines=true]" in out
    assert r"\end{lstlisting}" in out


def test_code_block_body_on_own_lines():
    # lstlisting reads code on the line after \begin and \end on its own line.
    out = Markdown(CODE).rendered
    assert "[breaklines=true]\ndef f():" in out
    assert 'margin"\n\\end{lstlisting}' in out


def test_code_block_omits_language():
    # listings aborts on unknown languages, so the info string is dropped.
    out = Markdown(CODE).rendered
    assert "language=" not in out


def test_code_block_pulls_in_listings_package():
    doc = Document(Markdown(CODE), document_class="article")
    assert "listings" in {p.name for p in doc.packages}
