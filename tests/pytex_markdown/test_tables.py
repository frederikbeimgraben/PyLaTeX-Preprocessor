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
    # The `X` columns at `\linewidth` make the content wrap. Without them the
    # content runs over the page edge. The `>{...}` prefixes hold the column
    # alignment.
    spec = (
        r">{\raggedright\arraybackslash}X"
        r">{\centering\arraybackslash}X"
        r">{\raggedleft\arraybackslash}X"
    )
    assert r"\begin{tabularx}{\linewidth}{" + spec + "}" in out
    assert r"\end{tabularx}" in out


def test_table_wrapped_in_vertical_space():
    # `\addvspace` adds vertical space above and below the table. It works
    # only in vertical mode, so `\par` comes first.
    out = Markdown(TABLE).rendered
    assert out.count(r"\par\addvspace{0.8\baselineskip}") == 2
    before = out.index(r"\par\addvspace{0.8\baselineskip}")
    after = out.rindex(r"\par\addvspace{0.8\baselineskip}")
    assert before < out.index(r"\begin{tabularx}")
    assert after > out.index(r"\end{tabularx}")


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
    # The converter makes a local image path absolute. The build compiles the
    # rendered `.tex` file in the build directory, not next to the Markdown
    # file. A relative path would not resolve there.
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
    # `lstlisting` reads the code from the line after `\begin`. The `\end`
    # needs its own line.
    out = Markdown(CODE).rendered
    assert "[breaklines=true]\ndef f():" in out
    assert 'margin"\n\\end{lstlisting}' in out


def test_code_block_omits_language():
    # listings stops with an error on a language it does not know, so the
    # converter drops the info string.
    out = Markdown(CODE).rendered
    assert "language=" not in out


def test_code_block_pulls_in_listings_package():
    doc = Document(Markdown(CODE), document_class="article")
    assert "listings" in {p.name for p in doc.packages}
