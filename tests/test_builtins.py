"""Tests for LaTeX builtin macros"""

import pytest

from model.builtins import (
    Bold,
    Href,
    Italic,
    Newline,
    Paragraph,
    Relax,
    Section,
    Subparagraph,
    Subsection,
    Subsubsection,
    Texttt,
)
from model.group import Group
from model.raw import Raw


class TestTextFormatting:
    """Test text formatting macros"""

    def test_bold(self):
        """Test Bold macro"""
        content = Raw("bold text")
        bold = Bold(content)
        serialized = bold.serialize()

        assert "\\textbf" in serialized
        assert "bold~text" in serialized
        assert "{" in serialized
        assert "}" in serialized

    def test_italic(self):
        """Test Italic macro"""
        content = Raw("italic text")
        italic = Italic(content)
        serialized = italic.serialize()

        assert "\\textit" in serialized
        assert "italic~text" in serialized

    def test_texttt(self):
        """Test Texttt (monospace) macro"""
        content = Raw("code text")
        texttt = Texttt(content)
        serialized = texttt.serialize()

        assert "\\texttt" in serialized
        assert "code~text" in serialized

    def test_nested_formatting(self):
        """Test nested text formatting"""
        inner = Bold(Raw("bold"))
        outer = Italic(inner)
        serialized = outer.serialize()

        assert "\\textit" in serialized
        assert "\\textbf" in serialized
        assert "bold" in serialized


class TestHeadings:
    """Test heading macros"""

    def test_section(self):
        """Test Section macro"""
        content = Raw("Section Title")
        section = Section(content)
        serialized = section.serialize()

        assert "\\section" in serialized
        assert "Section~Title" in serialized

    def test_subsection(self):
        """Test Subsection macro"""
        content = Raw("Subsection Title")
        subsection = Subsection(content)
        serialized = subsection.serialize()

        assert "\\subsection" in serialized
        assert "Subsection~Title" in serialized

    def test_subsubsection(self):
        """Test Subsubsection macro"""
        content = Raw("Subsubsection Title")
        subsubsection = Subsubsection(content)
        serialized = subsubsection.serialize()

        assert "\\subsubsection" in serialized
        assert "Subsubsection~Title" in serialized

    def test_paragraph(self):
        """Test Paragraph macro"""
        content = Raw("Paragraph Title")
        paragraph = Paragraph(content)
        serialized = paragraph.serialize()

        assert "\\paragraph" in serialized
        assert "Paragraph~Title" in serialized

    def test_subparagraph(self):
        """Test Subparagraph macro"""
        content = Raw("Subparagraph Title")
        subparagraph = Subparagraph(content)
        serialized = subparagraph.serialize()

        assert "\\subparagraph" in serialized
        assert "Subparagraph~Title" in serialized

    def test_heading_with_formatting(self):
        """Test heading with formatted text"""
        formatted = Bold(Raw("Bold Title"))
        section = Section(formatted)
        serialized = section.serialize()

        assert "\\section" in serialized
        assert "\\textbf" in serialized


class TestLinks:
    """Test link macros"""

    def test_href_simple(self):
        """Test Href macro with simple text"""
        url = Raw("https://example.com")
        text = Raw("Example Link")
        href = Href(url, text)
        serialized = href.serialize()

        assert "\\href" in serialized
        assert "https://example.com" in serialized
        assert "Example~Link" in serialized

    def test_href_with_formatting(self):
        """Test Href with formatted link text"""
        url = Raw("https://example.com")
        text = Bold(Raw("Bold Link"))
        href = Href(url, text)
        serialized = href.serialize()

        assert "\\href" in serialized
        assert "\\textbf" in serialized
        assert "Bold~Link" in serialized

    def test_href_special_chars_in_url(self):
        """Test Href with special characters in URL"""
        url = Raw("https://example.com/path?query=value&other=123")
        text = Raw("Link")
        href = Href(url, text)
        serialized = href.serialize()

        assert "\\href" in serialized
        # The URL should be preserved (Raw with safe=False handles this)


class TestUtilityMacros:
    """Test utility macros"""

    def test_relax(self):
        """Test Relax macro"""
        serialized = Relax.serialize()

        assert "\\relax" in serialized

    def test_newline(self):
        """Test Newline macro"""
        serialized = Newline.serialize()

        assert "\\\\" in serialized


class TestMacroChildren:
    """Test that macros correctly expose their children"""

    def test_bold_children(self):
        """Test Bold macro children property"""
        content = Raw("test")
        bold = Bold(content)
        children = bold.children

        assert len(children) == 1
        assert children[0] == content

    def test_section_children(self):
        """Test Section macro children property"""
        content = Raw("test")
        section = Section(content)
        children = section.children

        assert len(children) == 1
        assert children[0] == content

    def test_href_children(self):
        """Test Href macro children property"""
        url = Raw("url")
        text = Raw("text")
        href = Href(url, text)
        children = href.children

        assert len(children) == 2
        assert children[0] == url
        assert children[1] == text

    def test_relax_children(self):
        """Test Relax macro has no children"""
        children = Relax.children

        assert len(children) == 0


class TestMacroErrors:
    """Test error handling in macros"""

    def test_wrong_number_of_args_bold(self):
        """Test Bold with wrong number of arguments"""
        with pytest.raises(ValueError):
            Bold()  # pyright: ignore[reportCallIssue]  # Should require 1 argument

    def test_wrong_number_of_args_href(self):
        """Test Href with wrong number of arguments"""
        with pytest.raises(ValueError):
            Href(Raw("url"))  # pyright: ignore[reportCallIssue]  # Should require 2 arguments

    def test_wrong_number_of_args_section(self):
        """Test Section with wrong number of arguments"""
        with pytest.raises(ValueError):
            Section()  # pyright: ignore[reportCallIssue]  # Should require 1 argument


class TestComplexMacroUsage:
    """Test complex combinations of macros"""

    def test_formatted_section_with_link(self):
        """Test section containing a link with formatted text"""
        link_text = Bold(Raw("Bold Link"))
        link = Href(Raw("https://example.com"), link_text)
        section = Section(Group(Raw("Section with "), link))
        serialized = section.serialize()

        assert "\\section" in serialized
        assert "\\href" in serialized
        assert "\\textbf" in serialized

    def test_multiple_formatting_layers(self):
        """Test multiple layers of formatting"""
        text = Raw("text")
        bold = Bold(text)
        italic = Italic(bold)
        serialized = italic.serialize()

        assert "\\textit" in serialized
        assert "\\textbf" in serialized
        assert "text" in serialized

    def test_group_with_multiple_macros(self):
        """Test group containing multiple different macros"""
        group = Group(Bold(Raw("Bold ")), Italic(Raw("Italic ")), Texttt(Raw("Code")))
        serialized = group.serialize()

        assert "\\textbf" in serialized
        assert "\\textit" in serialized
        assert "\\texttt" in serialized


class TestSerialization:
    """Test that serialization produces valid LaTeX"""

    def test_bold_produces_valid_latex(self):
        """Test that Bold serialization is valid LaTeX"""
        bold = Bold(Raw("text"))
        serialized = bold.serialize()

        # Should match \textbf{text} pattern
        assert serialized.count("{") == serialized.count("}")
        assert "\\textbf" in serialized

    def test_section_produces_valid_latex(self):
        """Test that Section serialization is valid LaTeX"""
        section = Section(Raw("Title"))
        serialized = section.serialize()

        # Should match \section{Title} pattern
        assert serialized.count("{") == serialized.count("}")
        assert "\\section" in serialized

    def test_href_produces_valid_latex(self):
        """Test that Href serialization is valid LaTeX"""
        href = Href(Raw("url"), Raw("text"))
        serialized = href.serialize()

        # Should match \href{url}{text} pattern
        assert serialized.count("{") == serialized.count("}")
        assert "\\href" in serialized

    def test_nested_macros_produce_balanced_braces(self):
        """Test that nested macros produce balanced braces"""
        nested = Section(Bold(Italic(Raw("text"))))
        serialized = nested.serialize()

        assert serialized.count("{") == serialized.count("}")
