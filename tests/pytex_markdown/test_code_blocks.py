from pytex_markdown import Markdown


def test_fenced_code_renders_plain_lstlisting():
    out = Markdown("```\ndef demo():\n    return 42\n```").rendered
    assert r"\begin{lstlisting}[breaklines=true]" in out
    assert "def demo():" in out
    assert out.count(r"\end{lstlisting}") == 1


def test_fenced_code_cannot_break_out_of_lstlisting():
    # A fenced block that contains a line-start "\end{lstlisting}" must not
    # close the environment early. An early close would leave "\input{...}"
    # as live LaTeX instead of printed code.
    body = "text\n\\end{lstlisting}\n\\input{/etc/passwd}"
    out = Markdown(f"```\n{body}\n```").rendered
    # The environment must close exactly once, at the true end of the block,
    # with the quoted "\input" line still inside it as printed code.
    assert out.count(r"\end{lstlisting}") == 1
    assert out.endswith(r"\end{lstlisting}")
