"""Tests for LaTeX environment classes"""

from model.environment import (
    Enumerate,
    Environment,
    Item,
    Itemize,
    Quote,
    Verbatim,
)
from model.group import Group
from model.raw import Raw


class TestEnvironmentClass:
    """Test the Environment base class"""

    def test_environment_basic(self):
        """Test basic environment creation and serialization"""
        content = Raw("test content")
        env = Environment("testenv", content)
        serialized = env.serialize()

        assert serialized == "\\begin{testenv}\ntest content\n\\end{testenv}"

    def test_environment_with_complex_body(self):
        """Test environment with complex body content"""
        body = Group(Raw("First "), Raw("Second"))
        env = Environment("myenv", body)
        serialized = env.serialize()

        assert "\\begin{myenv}" in serialized
        assert "\\end{myenv}" in serialized
        assert "First" in serialized
        assert "Second" in serialized

    def test_environment_children(self):
        """Test environment children property"""
        content = Raw("test")
        env = Environment("testenv", content)
        children = env.children

        assert len(children) == 1
        assert children[0] == content

    def test_environment_nested(self):
        """Test nested environments"""
        inner = Environment("inner", Raw("inner content"))
        outer = Environment("outer", inner)
        serialized = outer.serialize()

        assert "\\begin{outer}" in serialized
        assert "\\begin{inner}" in serialized
        assert "\\end{inner}" in serialized
        assert "\\end{outer}" in serialized
        assert serialized.index("\\begin{outer}") < serialized.index("\\begin{inner}")
        assert serialized.index("\\end{inner}") < serialized.index("\\end{outer}")


class TestItemClass:
    """Test the Item class"""

    def test_item_basic(self):
        """Test basic item creation and serialization"""
        content = Raw("item content")
        item = Item(content)
        serialized = item.serialize()

        assert serialized == "\\item item content"

    def test_item_with_formatting(self):
        """Test item with formatted content"""
        from model.builtins import Bold

        content = Bold(Raw("bold item"))
        item = Item(content)
        serialized = item.serialize()

        assert "\\item" in serialized
        assert "\\textbf" in serialized
        assert "bold item" in serialized

    def test_item_children(self):
        """Test item children property"""
        content = Raw("test")
        item = Item(content)
        children = item.children

        assert len(children) == 1
        assert children[0] == content


class TestItemizeFunction:
    """Test the Itemize helper function"""

    def test_itemize_empty(self):
        """Test empty itemize"""
        itemize = Itemize()
        serialized = itemize.serialize()

        assert "\\begin{itemize}" in serialized
        assert "\\end{itemize}" in serialized

    def test_itemize_single_item(self):
        """Test itemize with single item"""
        item = Item(Raw("Single item"))
        itemize = Itemize(item)
        serialized = itemize.serialize()

        assert "\\begin{itemize}" in serialized
        assert "\\item Single item" in serialized
        assert "\\end{itemize}" in serialized

    def test_itemize_multiple_items(self):
        """Test itemize with multiple items"""
        items = [
            Item(Raw("First item")),
            Item(Raw("Second item")),
            Item(Raw("Third item")),
        ]
        itemize = Itemize(*items)
        serialized = itemize.serialize()

        assert "\\begin{itemize}" in serialized
        assert "\\item First item" in serialized
        assert "\\item Second item" in serialized
        assert "\\item Third item" in serialized
        assert "\\end{itemize}" in serialized

    def test_itemize_returns_environment(self):
        """Test that Itemize returns an Environment instance"""
        itemize = Itemize()

        assert isinstance(itemize, Environment)
        assert itemize.name == "itemize"


class TestEnumerateFunction:
    """Test the Enumerate helper function"""

    def test_enumerate_empty(self):
        """Test empty enumerate"""
        enumerate = Enumerate()
        serialized = enumerate.serialize()

        assert "\\begin{enumerate}" in serialized
        assert "\\end{enumerate}" in serialized

    def test_enumerate_single_item(self):
        """Test enumerate with single item"""
        item = Item(Raw("First"))
        enumerate = Enumerate(item)
        serialized = enumerate.serialize()

        assert "\\begin{enumerate}" in serialized
        assert "\\item First" in serialized
        assert "\\end{enumerate}" in serialized

    def test_enumerate_multiple_items(self):
        """Test enumerate with multiple items"""
        items = [
            Item(Raw("First")),
            Item(Raw("Second")),
            Item(Raw("Third")),
        ]
        enumerate = Enumerate(*items)
        serialized = enumerate.serialize()

        assert "\\begin{enumerate}" in serialized
        assert "\\item First" in serialized
        assert "\\item Second" in serialized
        assert "\\item Third" in serialized
        assert "\\end{enumerate}" in serialized

    def test_enumerate_returns_environment(self):
        """Test that Enumerate returns an Environment instance"""
        enumerate = Enumerate()

        assert isinstance(enumerate, Environment)
        assert enumerate.name == "enumerate"


class TestQuoteFunction:
    """Test the Quote helper function"""

    def test_quote_basic(self):
        """Test basic quote"""
        content = Raw("This is a quote")
        quote = Quote(content)
        serialized = quote.serialize()

        assert "\\begin{quote}" in serialized
        assert "This is a quote" in serialized
        assert "\\end{quote}" in serialized

    def test_quote_with_formatting(self):
        """Test quote with formatted content"""
        from model.builtins import Italic

        content = Italic(Raw("emphasized quote"))
        quote = Quote(content)
        serialized = quote.serialize()

        assert "\\begin{quote}" in serialized
        assert "\\textit" in serialized
        assert "emphasized quote" in serialized
        assert "\\end{quote}" in serialized

    def test_quote_returns_environment(self):
        """Test that Quote returns an Environment instance"""
        quote = Quote(Raw("test"))

        assert isinstance(quote, Environment)
        assert quote.name == "quote"


class TestVerbatimFunction:
    """Test the Verbatim helper function"""

    def test_verbatim_basic(self):
        """Test basic verbatim"""
        code = "print('hello')"
        verbatim = Verbatim(code)
        serialized = verbatim.serialize()

        assert "\\begin{verbatim}" in serialized
        assert "print('hello')" in serialized
        assert "\\end{verbatim}" in serialized

    def test_verbatim_multiline(self):
        """Test verbatim with multiline code"""
        code = """def hello():
    print("world")
    return True"""
        verbatim = Verbatim(code)
        serialized = verbatim.serialize()

        assert "\\begin{verbatim}" in serialized
        assert "def hello():" in serialized
        assert '    print("world")' in serialized
        assert "    return True" in serialized
        assert "\\end{verbatim}" in serialized

    def test_verbatim_with_special_chars(self):
        """Test verbatim with LaTeX special characters"""
        code = "$ & % # _ { } ~ ^ \\"
        verbatim = Verbatim(code)
        serialized = verbatim.serialize()

        assert "\\begin{verbatim}" in serialized
        # Special chars should be preserved in verbatim
        assert "$" in serialized
        assert "&" in serialized
        assert "%" in serialized
        assert "\\end{verbatim}" in serialized

    def test_verbatim_empty(self):
        """Test empty verbatim"""
        verbatim = Verbatim("")
        serialized = verbatim.serialize()

        assert "\\begin{verbatim}" in serialized
        assert "\\end{verbatim}" in serialized

    def test_verbatim_returns_environment(self):
        """Test that Verbatim returns an Environment instance"""
        verbatim = Verbatim("test")

        assert isinstance(verbatim, Environment)
        assert verbatim.name == "verbatim"


class TestNestedStructures:
    """Test complex nested structures with environments"""

    def test_list_with_nested_list(self):
        """Test list containing another list"""
        inner_items = [Item(Raw("Nested 1")), Item(Raw("Nested 2"))]
        inner_list = Itemize(*inner_items)
        outer_item = Item(Group(Raw("Outer item"), inner_list))
        outer_list = Itemize(outer_item)
        serialized = outer_list.serialize()

        assert serialized.count("\\begin{itemize}") == 2
        assert serialized.count("\\end{itemize}") == 2
        assert "Outer item" in serialized
        assert "Nested 1" in serialized

    def test_quote_with_list(self):
        """Test quote containing a list"""
        items = [Item(Raw("Point 1")), Item(Raw("Point 2"))]
        list_env = Itemize(*items)
        quote = Quote(Group(Raw("Introduction:"), list_env))
        serialized = quote.serialize()

        assert "\\begin{quote}" in serialized
        assert "\\begin{itemize}" in serialized
        assert "Introduction:" in serialized
        assert "\\end{itemize}" in serialized
        assert "\\end{quote}" in serialized

    def test_mixed_ordered_unordered_lists(self):
        """Test mixing ordered and unordered lists"""
        unordered = Itemize(Item(Raw("Bullet point")))
        ordered = Enumerate(Item(Raw("Numbered point")))
        group = Group(unordered, ordered)
        serialized = group.serialize()

        assert "\\begin{itemize}" in serialized
        assert "\\begin{enumerate}" in serialized
        assert "Bullet point" in serialized
        assert "Numbered point" in serialized


class TestEdgeCases:
    """Test edge cases for environments"""

    def test_environment_with_empty_name(self):
        """Test environment with empty name"""
        env = Environment("", Raw("content"))
        serialized = env.serialize()

        assert "\\begin{}" in serialized
        assert "\\end{}" in serialized

    def test_item_with_empty_content(self):
        """Test item with empty content"""
        item = Item(Raw(""))
        serialized = item.serialize()

        assert serialized == "\\item "

    def test_deeply_nested_environments(self):
        """Test deeply nested environments"""
        content = Raw("deepest")
        for i in range(5):
            content = Environment(f"level{i}", content)
        serialized = content.serialize()

        # Should have 5 levels of nesting
        assert serialized.count("\\begin{level") == 5
        assert serialized.count("\\end{level") == 5
        assert "deepest" in serialized
