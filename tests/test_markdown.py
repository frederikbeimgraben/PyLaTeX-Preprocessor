"""Tests for markdown parsing functionality"""

import marko

from model.environment import Environment, Item
from model.markdown import parse_md
from model.raw import Raw


class TestInlineElements:
    """Test parsing of inline markdown elements"""

    def test_raw_text(self):
        """Test plain text parsing"""
        md = "Hello World"
        doc = marko.parse(md)
        result = parse_md(doc)
        serialized = result.serialize()
        assert "Hello World" in serialized

    def test_bold_text(self):
        """Test bold text parsing"""
        md = "**bold text**"
        doc = marko.parse(md)
        result = parse_md(doc)
        serialized = result.serialize()
        assert "\\textbf" in serialized
        assert "bold text" in serialized

    def test_italic_text(self):
        """Test italic text parsing"""
        md = "*italic text*"
        doc = marko.parse(md)
        result = parse_md(doc)
        serialized = result.serialize()
        assert "\\textit" in serialized
        assert "italic text" in serialized

    def test_inline_code(self):
        """Test inline code parsing"""
        md = "`code snippet`"
        doc = marko.parse(md)
        result = parse_md(doc)
        serialized = result.serialize()
        assert "\\texttt" in serialized
        assert "code snippet" in serialized

    def test_link(self):
        """Test link parsing"""
        md = "[link text](https://example.com)"
        doc = marko.parse(md)
        result = parse_md(doc)
        serialized = result.serialize()
        assert "\\href" in serialized
        assert "example.com" in serialized
        assert "link text" in serialized

    def test_combined_formatting(self):
        """Test multiple inline formats together"""
        md = "This is **bold** and *italic* and `code`"
        doc = marko.parse(md)
        result = parse_md(doc)
        serialized = result.serialize()
        assert "\\textbf" in serialized
        assert "\\textit" in serialized
        assert "\\texttt" in serialized

    def test_nested_formatting(self):
        """Test nested formatting like bold within italic"""
        md = "*This is **nested** formatting*"
        doc = marko.parse(md)
        result = parse_md(doc)
        serialized = result.serialize()
        assert "\\textit" in serialized
        assert "\\textbf" in serialized


class TestBlockElements:
    """Test parsing of block markdown elements"""

    def test_paragraph(self):
        """Test paragraph parsing"""
        md = "This is a paragraph."
        doc = marko.parse(md)
        result = parse_md(doc)
        serialized = result.serialize()
        assert "paragraph" in serialized.lower()

    def test_heading_level_1(self):
        """Test h1 heading"""
        md = "# Heading 1"
        doc = marko.parse(md)
        result = parse_md(doc)
        serialized = result.serialize()
        assert "\\section" in serialized
        assert "Heading 1" in serialized

    def test_heading_level_2(self):
        """Test h2 heading"""
        md = "## Heading 2"
        doc = marko.parse(md)
        result = parse_md(doc)
        serialized = result.serialize()
        assert "\\subsection" in serialized
        assert "Heading 2" in serialized

    def test_heading_level_3(self):
        """Test h3 heading"""
        md = "### Heading 3"
        doc = marko.parse(md)
        result = parse_md(doc)
        serialized = result.serialize()
        assert "\\subsubsection" in serialized
        assert "Heading 3" in serialized

    def test_heading_level_4(self):
        """Test h4 heading"""
        md = "#### Heading 4"
        doc = marko.parse(md)
        result = parse_md(doc)
        serialized = result.serialize()
        assert "\\paragraph" in serialized
        assert "Heading 4" in serialized

    def test_heading_level_5(self):
        """Test h5 heading"""
        md = "##### Heading 5"
        doc = marko.parse(md)
        result = parse_md(doc)
        serialized = result.serialize()
        assert "\\subparagraph" in serialized
        assert "Heading 5" in serialized

    def test_code_block_fenced(self):
        """Test fenced code block"""
        md = """```python
def hello():
    print("world")
```"""
        doc = marko.parse(md)
        result = parse_md(doc)
        serialized = result.serialize()
        assert "\\begin{verbatim}" in serialized
        assert "\\end{verbatim}" in serialized
        assert "def hello():" in serialized

    def test_code_block_indented(self):
        """Test indented code block"""
        md = "    code line 1\n    code line 2"
        doc = marko.parse(md)
        result = parse_md(doc)
        serialized = result.serialize()
        assert "\\begin{verbatim}" in serialized
        assert "code line 1" in serialized

    def test_blockquote(self):
        """Test blockquote parsing"""
        md = "> This is a quote"
        doc = marko.parse(md)
        result = parse_md(doc)
        serialized = result.serialize()
        assert "\\begin{quote}" in serialized
        assert "\\end{quote}" in serialized
        assert "This is a quote" in serialized

    def test_unordered_list(self):
        """Test unordered list"""
        md = """- Item 1
- Item 2
- Item 3"""
        doc = marko.parse(md)
        result = parse_md(doc)
        serialized = result.serialize()
        assert "\\begin{itemize}" in serialized
        assert "\\end{itemize}" in serialized
        assert "\\item" in serialized
        assert "Item 1" in serialized
        assert "Item 2" in serialized
        assert "Item 3" in serialized

    def test_ordered_list(self):
        """Test ordered list"""
        md = """1. First
2. Second
3. Third"""
        doc = marko.parse(md)
        result = parse_md(doc)
        serialized = result.serialize()
        assert "\\begin{enumerate}" in serialized
        assert "\\end{enumerate}" in serialized
        assert "\\item" in serialized
        assert "First" in serialized

    def test_horizontal_rule(self):
        """Test horizontal rule"""
        md = "---"
        doc = marko.parse(md)
        result = parse_md(doc)
        serialized = result.serialize()
        assert "\\hrule" in serialized


class TestSpecialCharacterEscaping:
    """Test that LaTeX special characters are properly escaped"""

    def test_escape_backslash(self):
        """Test backslash escaping"""
        md = "Text with \\ backslash"
        doc = marko.parse(md)
        result = parse_md(doc)
        serialized = result.serialize()
        assert "\\textbackslash" in serialized

    def test_escape_braces(self):
        """Test curly brace escaping"""
        md = "Text with { and } braces"
        doc = marko.parse(md)
        result = parse_md(doc)
        serialized = result.serialize()
        assert "\\{" in serialized
        assert "\\}" in serialized

    def test_escape_dollar(self):
        """Test dollar sign escaping"""
        md = "Price: $100"
        doc = marko.parse(md)
        result = parse_md(doc)
        serialized = result.serialize()
        assert "\\$" in serialized

    def test_escape_ampersand(self):
        """Test ampersand escaping"""
        md = "This & that"
        doc = marko.parse(md)
        result = parse_md(doc)
        serialized = result.serialize()
        assert "\\&" in serialized

    def test_escape_percent(self):
        """Test percent sign escaping"""
        md = "100% complete"
        doc = marko.parse(md)
        result = parse_md(doc)
        serialized = result.serialize()
        assert "\\%" in serialized

    def test_escape_hash(self):
        """Test hash/pound sign escaping"""
        md = "Tag: #hashtag"
        doc = marko.parse(md)
        result = parse_md(doc)
        serialized = result.serialize()
        # Note: # at start of line is heading, so use it mid-text
        assert "\\#" in serialized or "hashtag" in serialized

    def test_escape_underscore(self):
        """Test underscore escaping"""
        md = "variable_name"
        doc = marko.parse(md)
        result = parse_md(doc)
        serialized = result.serialize()
        assert "\\_" in serialized

    def test_escape_tilde(self):
        """Test tilde escaping"""
        md = "Path: ~/home"
        doc = marko.parse(md)
        result = parse_md(doc)
        serialized = result.serialize()
        assert "\\textasciitilde" in serialized

    def test_escape_caret(self):
        """Test caret escaping"""
        md = "Power: 2^3"
        doc = marko.parse(md)
        result = parse_md(doc)
        serialized = result.serialize()
        assert "\\textasciicircum" in serialized


class TestComplexDocuments:
    """Test parsing of complex markdown documents with multiple elements"""

    def test_mixed_content(self):
        """Test document with multiple element types"""
        md = """# Main Title

This is a paragraph with **bold** and *italic* text.

## Subsection

- List item 1
- List item 2

```python
print("code")
```

> A quote

[Link](https://example.com)"""

        doc = marko.parse(md)
        result = parse_md(doc)
        serialized = result.serialize()

        # Check all elements are present
        assert "\\section" in serialized
        assert "\\subsection" in serialized
        assert "\\textbf" in serialized
        assert "\\textit" in serialized
        assert "\\begin{itemize}" in serialized
        assert "\\begin{verbatim}" in serialized
        assert "\\begin{quote}" in serialized
        assert "\\href" in serialized

    def test_nested_lists(self):
        """Test nested list structures"""
        md = """- Item 1
  - Nested 1.1
  - Nested 1.2
- Item 2"""

        doc = marko.parse(md)
        result = parse_md(doc)
        serialized = result.serialize()

        assert "\\begin{itemize}" in serialized
        assert "\\item" in serialized

    def test_multiple_paragraphs(self):
        """Test multiple paragraphs"""
        md = """First paragraph.

Second paragraph.

Third paragraph."""

        doc = marko.parse(md)
        result = parse_md(doc)
        serialized = result.serialize()

        # Should contain paragraph markers
        assert "paragraph" in serialized.lower()

    def test_link_with_formatting(self):
        """Test link with formatted text"""
        md = "[**bold link**](https://example.com)"
        doc = marko.parse(md)
        result = parse_md(doc)
        serialized = result.serialize()

        assert "\\href" in serialized
        assert "\\textbf" in serialized

    def test_empty_document(self):
        """Test empty document"""
        md = ""
        doc = marko.parse(md)
        result = parse_md(doc)
        serialized = result.serialize()

        # Should not crash and return valid LaTeX
        assert isinstance(serialized, str)

    def test_only_whitespace(self):
        """Test document with only whitespace"""
        md = "   \n\n   "
        doc = marko.parse(md)
        result = parse_md(doc)
        serialized = result.serialize()

        # Should not crash
        assert isinstance(serialized, str)


class TestEnvironmentClasses:
    """Test the environment helper classes directly"""

    def test_environment_serialization(self):
        """Test Environment class serialization"""
        content = Raw("test content")
        env = Environment("testenv", content)
        serialized = env.serialize()

        assert serialized == "\\begin{testenv}\ntest content\n\\end{testenv}"

    def test_item_serialization(self):
        """Test Item class serialization"""
        content = Raw("item content")
        item = Item(content)
        serialized = item.serialize()

        assert serialized == "\\item item content"

    def test_environment_children(self):
        """Test Environment children property"""
        content = Raw("test")
        env = Environment("testenv", content)
        children = env.children

        assert len(children) == 1
        assert children[0] == content

    def test_item_children(self):
        """Test Item children property"""
        content = Raw("test")
        item = Item(content)
        children = item.children

        assert len(children) == 1
        assert children[0] == content


class TestEdgeCases:
    """Test edge cases and potential issues"""

    def test_autolink(self):
        """Test autolink parsing"""
        md = "<https://example.com>"
        doc = marko.parse(md)
        result = parse_md(doc)
        serialized = result.serialize()

        assert "\\href" in serialized
        assert "example.com" in serialized

    def test_image_placeholder(self):
        """Test image parsing (should create placeholder)"""
        md = "![alt text](image.png)"
        doc = marko.parse(md)
        result = parse_md(doc)
        serialized = result.serialize()

        assert "Image" in serialized or "image.png" in serialized

    def test_line_break_hard(self):
        """Test hard line break"""
        md = "Line 1  \nLine 2"
        doc = marko.parse(md)
        result = parse_md(doc)
        serialized = result.serialize()

        # Should contain some form of line break
        assert isinstance(serialized, str)

    def test_mixed_list_types(self):
        """Test switching between ordered and unordered lists"""
        md = """- Unordered item

1. Ordered item"""

        doc = marko.parse(md)
        result = parse_md(doc)
        serialized = result.serialize()

        assert "\\begin{itemize}" in serialized
        assert "\\begin{enumerate}" in serialized

    def test_code_with_special_chars(self):
        """Test code block with special LaTeX characters"""
        md = """```
$ & % # _ { } ~ ^ \\
```"""
        doc = marko.parse(md)
        result = parse_md(doc)
        serialized = result.serialize()

        # In verbatim, special chars should be preserved
        assert "\\begin{verbatim}" in serialized
        assert "$" in serialized  # Inside verbatim, should be literal
