"""File inclusion and raw TeX support.

Provides classes for including external files (both .tex and .pytex)
and inserting raw LaTeX code into documents.
"""

from dataclasses import dataclass
from pathlib import Path
from typing import override

from model.base_model import TeX


@dataclass
class RawTeX(TeX):
    """Raw LaTeX content that will be included verbatim.

    Unlike Raw, RawTeX:
    - Does not escape spaces by default
    - Is intended for including raw LaTeX fragments
    - Does not validate brace balance

    Args:
        content: Raw LaTeX string to include
        escape_spaces: Whether to escape spaces (default: False)

    Example:
        RawTeX(r"\\customcommand[option]{arg}")
    """

    content: str
    escape_spaces: bool = False

    @property
    @override
    def children(self) -> tuple["TeX", ...]:
        return tuple()

    @override
    def serialize(self, indent: int = 0) -> str:
        """Serialize with optional indentation.

        Args:
            indent: Indentation level (ignored for raw TeX)

        Returns:
            Serialized string
        """
        return self.serialize_indented(indent)

    def serialize_indented(self, _indent: int) -> str:
        """Serialize with indentation.

        Args:
            indent: Indentation level (ignored for raw TeX)

        Returns:
            Serialized string
        """
        if self.escape_spaces:
            return self.content.replace(" ", "~")
        return self.content


@dataclass
class IncludeTeX(TeX):
    """Include an external .tex file.

    Uses LaTeX's \\input command to include the contents of another
    LaTeX file at this position.

    Args:
        path: Path to the .tex file (relative or absolute)

    Example:
        IncludeTeX("sections/introduction.tex")

    Note:
        The .tex extension can be omitted in LaTeX; it will be inferred.
    """

    path: str | Path

    @property
    @override
    def children(self) -> tuple["TeX", ...]:
        return tuple()

    @override
    def serialize(self, indent: int = 0) -> str:
        r"""Serialize with optional indentation.

        Args:
            indent: Indentation level (ignored for includes)

        Returns:
            Serialized LaTeX \input command
        """
        return self.serialize_indented(indent)

    def serialize_indented(self, _indent: int) -> str:
        r"""Serialize with indentation.

        Args:
            indent: Indentation level (ignored for includes)

        Returns:
            Serialized LaTeX \input command
        """
        # Convert Path to string and remove .tex extension if present
        # LaTeX's \input automatically adds .tex
        path_str = str(self.path)
        if path_str.endswith(".tex"):
            path_str = path_str[:-4]
        return f"\\input{{{path_str}}}"


@dataclass
class Include(TeX):
    """Include an external .pytex file.

    Loads a Python-syntax TeX tree from a .pytex file and includes it
    inline in the document. The .pytex file should define a single TeX
    object in its namespace.

    Args:
        path: Path to the .pytex file

    Example:
        # In document:
        Include("sections/introduction.pytex")

        # In sections/introduction.pytex:
        Section(Raw("Introduction"))

    Note:
        This is evaluated at document build time, not LaTeX compile time.
        The .pytex file must be valid Python that evaluates to a TeX object.
    """

    path: str | Path
    _cached_content: TeX | None = None

    @property
    @override
    def children(self) -> tuple["TeX", ...]:
        if self._cached_content is not None:
            return (self._cached_content,)
        return tuple()

    def load(self) -> TeX:
        """Load and parse the .pytex file.

        Returns:
            The TeX object defined in the .pytex file

        Raises:
            FileNotFoundError: If the file doesn't exist
            ValueError: If the file doesn't evaluate to a TeX object
        """
        from pathlib import Path

        path = Path(self.path)
        if not path.exists():
            raise FileNotFoundError(f"File not found: {path}")

        # Read and execute the .pytex file
        with open(path) as f:
            code = f.read()

        # Create a namespace with our model imports available
        namespace: dict[str, object] = {}

        # Import everything that's available in .pytex files
        # This makes all symbols available without prefix
        from library.builtins import (
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
        from library.document import Document
        from library.document_builtins import MakeTitle, NewPage, TableOfContents
        from library.environments import (
            Enumerate,
            Environment,
            Item,
            Itemize,
            Quote,
            Verbatim,
        )
        from library.inclusion import Include, IncludeTeX, RawTeX
        from model.base_model import Package, TeX
        from model.group import Group
        from model.raw import Raw

        namespace.update(
            {
                "TeX": TeX,
                "Package": Package,
                "Raw": Raw,
                "Group": Group,
                "Document": Document,
                "MakeTitle": MakeTitle,
                "TableOfContents": TableOfContents,
                "NewPage": NewPage,
                "Bold": Bold,
                "Italic": Italic,
                "Texttt": Texttt,
                "Section": Section,
                "Subsection": Subsection,
                "Subsubsection": Subsubsection,
                "Paragraph": Paragraph,
                "Subparagraph": Subparagraph,
                "Href": Href,
                "Newline": Newline,
                "Relax": Relax,
                "Environment": Environment,
                "Item": Item,
                "Itemize": Itemize,
                "Enumerate": Enumerate,
                "Quote": Quote,
                "Verbatim": Verbatim,
                "Include": Include,
                "IncludeTeX": IncludeTeX,
                "RawTeX": RawTeX,
                # Allow standard library imports
                "__builtins__": __builtins__,
            }
        )

        # Execute the code
        exec(code, namespace)

        # Find the TeX object in the namespace
        # Look for a variable named 'document', 'content', or the first TeX object
        result: TeX | None = None
        for name in ["document", "content", "root"]:
            if name in namespace:
                obj = namespace[name]
                if isinstance(obj, TeX):
                    result = obj
                    break

        if result is None:
            # Find any TeX object in the namespace
            for value in namespace.values():
                if isinstance(value, TeX):
                    result = value
                    break

        if result is None:
            msg = (
                f"No TeX object found in {path}. "
                "Define a TeX object named 'document', 'content', or 'root'."
            )
            raise ValueError(msg)

        self._cached_content = result
        return result

    @override
    def serialize(self, indent: int = 0) -> str:
        """Serialize with optional indentation.

        Args:
            indent: Indentation level (passed to loaded content)

        Returns:
            Serialized content from the .pytex file
        """
        return self.serialize_indented(indent)

    def serialize_indented(self, indent: int) -> str:
        """Serialize with indentation.

        Args:
            indent: Indentation level (passed to loaded content)

        Returns:
            Serialized content from the .pytex file
        """
        from model.serialization import serialize_with_indent

        if self._cached_content is None:
            self._cached_content = self.load()
        return serialize_with_indent(self._cached_content, indent)
