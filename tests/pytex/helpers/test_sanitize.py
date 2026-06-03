from pytex.helpers.sanitize import escape_latex


def test_double_quote_escaped():
    # babel ngerman makes `"` an active shorthand, so it must not pass through.
    assert escape_latex('say "hi"') == r"say \textquotedbl{}hi\textquotedbl{}"
    assert '"' not in escape_latex('"')


def test_quote_escape_keeps_surrounding_text():
    assert escape_latex('a"b') == r"a\textquotedbl{}b"


def test_existing_specials_still_escaped():
    # Guard the new entry did not disturb the existing escape table.
    assert escape_latex("100% & _x_") == r"100\% \& \_x\_"
