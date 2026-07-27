from pytex.helpers.sanitize import escape_latex


def test_double_quote_escaped():
    # PyTeX loads babel with the `ngerman` option. That option makes `"` an
    # active shorthand character. A literal `"` must not reach the rendered
    # `.tex` file.
    assert escape_latex('say "hi"') == r"say \textquotedbl{}hi\textquotedbl{}"
    assert '"' not in escape_latex('"')


def test_quote_escape_keeps_surrounding_text():
    assert escape_latex('a"b') == r"a\textquotedbl{}b"


def test_existing_specials_still_escaped():
    # The `"` entry is the newest entry in the escape table. This test makes
    # sure that entry did not break the older entries.
    assert escape_latex("100% & _x_") == r"100\% \& \_x\_"
