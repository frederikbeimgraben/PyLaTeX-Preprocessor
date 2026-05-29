"""Tests demonstrating type safety of strongly-typed builtin macros.

This test suite validates that the strongly-typed macro classes provide
proper compile-time and runtime type checking.
"""

import pytest

from pytex import (
    Bold,
    Group,
    Href,
    Italic,
    Newline,
    Paragraph,
    Raw,
    Relax,
    Section,
    Subparagraph,
    Subsection,
    Subsubsection,
    Texttt,
)


class TestTypeSignatures:
    """Test that macros have proper type signatures."""

    def test_bold_accepts_tex_content(self):
        """Bold should accept any TeX content."""
        # All these should work
        Bold(Raw("text"))
        Bold(Italic(Raw("text")))
        Bold(Texttt(Raw("text")))

    def test_section_accepts_tex_content(self):
        """Section should accept any TeX content."""
        # All these should work
        Section(Raw("Title"))
        Section(Bold(Raw("Bold Title")))
        Section(Italic(Raw("Italic Title")))

    def test_href_requires_two_args(self):
        """Href requires exactly two TeX arguments."""
        # Should work
        Href(Raw("url"), Raw("text"))
        Href(Raw("url"), Bold(Raw("text")))

        # Should fail with wrong number of args
        with pytest.raises(ValueError):
            Href(Raw("url"))  # pyright: ignore[reportCallIssue]

        with pytest.raises(ValueError):
            Href(Raw("url"), Raw("text"), Raw("extra"))  # pyright: ignore[reportCallIssue]

    def test_relax_takes_no_args(self):
        """Relax is a singleton that takes no arguments."""
        # Relax is already instantiated
        assert Relax.serialize() == "\\relax\\relax "

    def test_newline_takes_no_args(self):
        """Newline is a singleton that takes no arguments."""
        # Newline is already instantiated
        assert "\\\\" in Newline.serialize()


class TestRuntimeTypeChecking:
    """Test that runtime type checking works correctly."""

    def test_wrong_arg_count_raises_valueerror(self):
        """Providing wrong number of arguments raises ValueError."""
        with pytest.raises(ValueError, match="Invalid parameter count"):
            Bold()  # pyright: ignore[reportCallIssue]  # Needs 1 arg

        with pytest.raises(ValueError, match="Invalid parameter count"):
            Bold(Raw("a"), Raw("b"))  # pyright: ignore[reportCallIssue]  # Needs 1 arg, got 2

        with pytest.raises(ValueError, match="Invalid parameter count"):
            Section()  # pyright: ignore[reportCallIssue]  # Needs 1 arg

        with pytest.raises(ValueError, match="Invalid parameter count"):
            Href(Raw("url"))  # pyright: ignore[reportCallIssue]  # Needs 2 args

    def test_all_single_arg_macros(self):
        """Test all single-argument macros accept exactly one arg."""
        single_arg_macros = [
            Bold,
            Italic,
            Texttt,
            Section,
            Subsection,
            Subsubsection,
            Paragraph,
            Subparagraph,
        ]

        for MacroClass in single_arg_macros:
            # Should work with one argument
            macro = MacroClass(Raw("test"))
            assert len(macro.children) == 1

            # Should fail with zero arguments
            with pytest.raises(ValueError):
                MacroClass()  # pyright: ignore[reportCallIssue]

            # Should fail with two arguments
            with pytest.raises(ValueError):
                MacroClass(Raw("a"), Raw("b"))  # pyright: ignore[reportCallIssue]


class TestTypeConsistency:
    """Test that macros maintain type consistency."""

    def test_children_property_matches_args(self):
        """The children property should match the provided arguments."""
        content = Raw("test")
        bold = Bold(content)

        assert bold.children == (content,)
        assert len(bold.children) == 1
        assert bold.children[0] is content

    def test_nested_macros_maintain_types(self):
        """Nested macros should maintain proper type hierarchy."""
        inner = Raw("text")
        italic = Italic(inner)
        bold = Bold(italic)
        section = Section(bold)

        # Each level should properly wrap the previous
        assert section.children[0] is bold
        assert bold.children[0] is italic
        assert italic.children[0] is inner

    def test_href_maintains_both_arguments(self):
        """Href should maintain both URL and text arguments."""
        url = Raw("https://example.com")
        text = Raw("Link Text")
        href = Href(url, text)

        assert len(href.children) == 2
        assert href.children[0] is url
        assert href.children[1] is text


class TestMacroProperties:
    """Test that macro properties are correctly defined."""

    def test_macro_id_property(self):
        """Each macro should have the correct LaTeX command id."""
        assert Bold(Raw("x")).id == "textbf"
        assert Italic(Raw("x")).id == "textit"
        assert Texttt(Raw("x")).id == "texttt"
        assert Section(Raw("x")).id == "section"
        assert Subsection(Raw("x")).id == "subsection"
        assert Subsubsection(Raw("x")).id == "subsubsection"
        assert Paragraph(Raw("x")).id == "paragraph"
        assert Subparagraph(Raw("x")).id == "subparagraph"
        assert Href(Raw("a"), Raw("b")).id == "href"
        assert Relax.id == "relax"
        assert Newline.id == "\\"

    def test_n_positional_property(self):
        """Each macro should report correct positional argument count."""
        assert Bold(Raw("x")).n_positional == 1
        assert Italic(Raw("x")).n_positional == 1
        assert Texttt(Raw("x")).n_positional == 1
        assert Section(Raw("x")).n_positional == 1
        assert Subsection(Raw("x")).n_positional == 1
        assert Subsubsection(Raw("x")).n_positional == 1
        assert Paragraph(Raw("x")).n_positional == 1
        assert Subparagraph(Raw("x")).n_positional == 1
        assert Href(Raw("a"), Raw("b")).n_positional == 2
        assert Relax.n_positional == 0
        assert Newline.n_positional == 0

    def test_keyword_args_property(self):
        """Macros should have empty keyword_args by default."""
        assert Bold(Raw("x")).keyword_args == {}
        assert Italic(Raw("x")).keyword_args == {}
        assert Section(Raw("x")).keyword_args == {}
        assert Href(Raw("a"), Raw("b")).keyword_args == {}
        assert Relax.keyword_args == {}


class TestDocumentation:
    """Test that macros have proper documentation."""

    def test_classes_have_docstrings(self):
        """All macro classes should have docstrings."""
        assert Bold.__doc__ is not None
        assert "textbf" in Bold.__doc__

        assert Italic.__doc__ is not None
        assert "textit" in Italic.__doc__

        assert Section.__doc__ is not None
        assert "section" in Section.__doc__

        assert Href.__doc__ is not None
        assert "href" in Href.__doc__

    def test_docstrings_contain_examples(self):
        """Macro docstrings should contain usage examples."""
        assert Bold.__doc__ is not None and "Example:" in Bold.__doc__
        assert Italic.__doc__ is not None and "Example:" in Italic.__doc__
        assert Section.__doc__ is not None and "Example:" in Section.__doc__
        assert Href.__doc__ is not None and "Example:" in Href.__doc__


class TestSingletonMacros:
    """Test that singleton macros (Relax, Newline) work correctly."""

    def test_relax_is_singleton(self):
        """Relax should be a pre-instantiated singleton."""
        # Relax is already an instance, not a class
        assert Relax.id == "relax"
        assert Relax.n_positional == 0
        assert len(Relax.children) == 0

    def test_newline_is_singleton(self):
        """Newline should be a pre-instantiated singleton."""
        # Newline is already an instance, not a class
        assert Newline.id == "\\"
        assert Newline.n_positional == 0
        assert len(Newline.children) == 0

    def test_singletons_serialize_correctly(self):
        """Singleton macros should serialize without arguments."""
        relax_output = Relax.serialize()
        assert "\\relax" in relax_output
        assert "{" not in relax_output  # No argument braces

        newline_output = Newline.serialize()
        assert "\\\\" in newline_output
        assert "{" not in newline_output  # No argument braces


class TestComplexTypeInteractions:
    """Test complex interactions between strongly-typed macros."""

    def test_deeply_nested_formatting(self):
        """Test multiple levels of nested formatting maintain types."""
        # Create: Section(Bold(Italic(Texttt(Raw("text")))))
        innermost = Raw("code")
        mono = Texttt(innermost)
        italic = Italic(mono)
        bold = Bold(italic)
        section = Section(bold)

        # Verify structure
        assert section.children[0] is bold
        assert bold.children[0] is italic
        assert italic.children[0] is mono
        assert mono.children[0] is innermost

        # Verify serialization contains all commands
        output = section.serialize()
        assert "\\section" in output
        assert "\\textbf" in output
        assert "\\textit" in output
        assert "\\texttt" in output

    def test_mixed_macro_types_in_sequence(self):
        """Test that different macro types can coexist properly."""
        # Create a group with various macro types
        group = Group(
            Section(Raw("Title")),
            Bold(Raw("Bold")),
            Italic(Raw("Italic")),
            Href(Raw("url"), Raw("link")),
            Texttt(Raw("code")),
        )

        output = group.serialize()
        assert "\\section" in output
        assert "\\textbf" in output
        assert "\\textit" in output
        assert "\\href" in output
        assert "\\texttt" in output


class TestBackwardCompatibility:
    """Test that new strongly-typed macros maintain backward compatibility."""

    def test_serialization_format_unchanged(self):
        """Serialization format should match previous SimpleMacro output."""
        # These patterns should still work
        bold = Bold(Raw("text"))
        assert "\\textbf{" in bold.serialize()
        assert "text" in bold.serialize()

        section = Section(Raw("Title"))
        assert "\\section{" in section.serialize()
        assert "Title" in section.serialize()

        href = Href(Raw("url"), Raw("text"))
        assert "\\href{" in href.serialize()
        assert "url" in href.serialize()
        assert "text" in href.serialize()

    def test_children_api_unchanged(self):
        """The children property API should remain the same."""
        bold = Bold(Raw("x"))
        assert hasattr(bold, "children")
        assert isinstance(bold.children, tuple)

        href = Href(Raw("a"), Raw("b"))
        assert hasattr(href, "children")
        assert isinstance(href.children, tuple)
        assert len(href.children) == 2
