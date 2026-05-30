"""Tests for the HSRT markdown callout parser."""

from pytex_hsrtreport import markdown_to_tex


class TestCallouts:
    def test_info_callout(self):
        # ColoredBox is a native pytex node — no environment, just inline
        # mdframed contents with the icon baked in.
        out = markdown_to_tex("> [!INFO]\n> Be informed.").serialize()
        assert "\\begin{mdframed}" in out
        assert "\\faInfoCircle" in out
        assert "Be" in out
        assert "[!INFO]" not in out

    def test_warning_callout(self):
        out = markdown_to_tex("> [!WARNING]\n> Careful here.").serialize()
        assert "\\begin{mdframed}" in out
        assert "\\faExclamationTriangle" in out

    def test_tip_is_success_box(self):
        out = markdown_to_tex("> [!TIP]\n> Nice trick.").serialize()
        assert "\\begin{mdframed}" in out
        assert "\\faCheckCircle" in out

    def test_plain_quote_not_a_callout(self):
        out = markdown_to_tex("> just a quote").serialize()
        assert "InfoBox" not in out
        assert "\\begin{quote}" in out


class TestCodeFences:
    def test_fenced_code_with_language_is_listing(self):
        out = markdown_to_tex("```python\nprint(1)\n```").serialize()
        assert "\\begin{lstlisting}[language={python}]" in out
        assert "print(1)" in out

    def test_fenced_code_without_language_is_verbatim(self):
        out = markdown_to_tex("```\nplain\n```").serialize()
        assert "\\begin{verbatim}" in out


class TestFallback:
    def test_headings_and_bold(self):
        out = markdown_to_tex("# Title\n\nSome **bold** text.").serialize()
        assert "\\section{" in out
        assert "\\textbf{" in out
