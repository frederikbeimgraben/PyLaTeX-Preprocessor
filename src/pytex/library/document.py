"""High-level Document abstraction for LaTeX.

Provides the Document class that handles document structure, package management,
metadata (title, author, date), and automatic preamble generation.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import override

from ..model.base_model import Package, TeX
from ..model.raw import Raw
from .packages import (
    collect_packages,
    resolve_package_dependencies,
    serialize_usepackage,
)


@dataclass
class Document(TeX):
    """High-level LaTeX document with automatic preamble generation.

    Handles document structure, package management, metadata, and generates
    a complete LaTeX document with proper preamble.

    Args:
        document_class: Document class (e.g., "article", "report", "book")
        content: Main document content
        preamble: Optional additional preamble content (inserted after packages)
        title: Document title (str or TeX object)
        toc: Whether to include table of contents
        author: Document author (str or TeX object)
        date: Document date (str, datetime, or TeX object). None = \\today
        packages: Set of packages to include (Package objects or strings)
        class_options: Options passed to \\documentclass[...] (e.g. ["12pt", "a4paper"])

    Example:
        Document(
            document_class="article",
            content=Group(
                Section(Raw("Introduction")),
                Raw("Hello, world!")
            ),
            title="My Document",
            author="John Doe",
            toc=True,
            packages={"amsmath", "graphicx"},
            class_options=["12pt", "a4paper"],
        )
    """

    document_class: str | Package
    content: TeX
    preamble: TeX | None = None
    title: str | TeX | None = None
    toc: bool = False
    author: str | TeX | None = None
    date: str | datetime | TeX | None = None
    packages: set[Package | str] = field(default_factory=set)
    class_options: list[str] = field(default_factory=list)
    manage_packages: bool = True
    """When False, no ``\\usepackage`` lines are auto-generated; the preamble is
    expected to load every package itself (e.g. to control package options)."""

    @property
    @override
    def children(self) -> tuple["TeX", ...]:
        children = [self.content]
        if self.preamble is not None:
            children.insert(0, self.preamble)
        return tuple(children)

    def _get_document_class_name(self) -> str:
        """Get the document class name as a string."""
        if isinstance(self.document_class, Package):
            return self.document_class.name
        return self.document_class

    def _normalize_metadata(self, value: str | TeX | None) -> TeX | None:
        """Convert string metadata to TeX objects."""
        if value is None or isinstance(value, TeX):
            return value
        return Raw(value)

    def _format_date(self, date: str | datetime | TeX | None) -> TeX | None:
        """Format date field appropriately."""
        if date is None:
            return None  # Will use \today in LaTeX
        if isinstance(date, TeX):
            return date
        if isinstance(date, datetime):
            return Raw(date.strftime("%B %d, %Y"))
        return Raw(date)

    def _generate_preamble_content(self) -> list[TeX]:
        """Generate preamble content including packages and metadata."""
        preamble_parts: list[TeX] = []

        if self.manage_packages:
            # Collect all packages (from explicit list + from content tree)
            all_packages = set(self.packages)
            all_packages.update(collect_packages(self.content))
            if self.preamble:
                all_packages.update(collect_packages(self.preamble))

            # Resolve dependencies and conflicts
            resolved_packages = resolve_package_dependencies(all_packages)

            # Generate \usepackage commands
            for pkg in resolved_packages:
                preamble_parts.append(
                    Raw(
                        f"{serialize_usepackage(pkg)}\n",
                        escape_spaces=False,
                        safe=False,
                    )
                )

        # Add custom preamble content if provided
        if self.preamble is not None:
            preamble_parts.append(self.preamble)

        # Add metadata commands
        title = self._normalize_metadata(self.title)
        author = self._normalize_metadata(self.author)
        date = self._format_date(self.date)

        if title is not None:
            preamble_parts.append(Raw("\\title{", escape_spaces=False, safe=False))
            preamble_parts.append(title)
            preamble_parts.append(Raw("}\n", escape_spaces=False, safe=False))

        if author is not None:
            preamble_parts.append(Raw("\\author{", escape_spaces=False, safe=False))
            preamble_parts.append(author)
            preamble_parts.append(Raw("}\n", escape_spaces=False, safe=False))

        if date is not None:
            preamble_parts.append(Raw("\\date{", escape_spaces=False, safe=False))
            preamble_parts.append(date)
            preamble_parts.append(Raw("}\n", escape_spaces=False, safe=False))

        return preamble_parts

    def _generate_document_content(self) -> list[TeX]:
        """Generate document body content."""
        from .document_builtins import MakeTitle, TableOfContents

        body_parts: list[TeX] = []

        # Add \maketitle if we have metadata
        if self.title is not None or self.author is not None or self.date is not None:
            body_parts.append(MakeTitle)
            body_parts.append(Raw("\n", escape_spaces=False, safe=False))

        # Add table of contents if requested
        if self.toc:
            body_parts.append(TableOfContents)
            body_parts.append(Raw("\n", escape_spaces=False, safe=False))

        # Add main content
        body_parts.append(self.content)

        return body_parts

    @override
    def serialize(self) -> str:
        """Generate the complete LaTeX document."""
        doc_class = self._get_document_class_name()

        # Build preamble
        preamble_parts = self._generate_preamble_content()
        preamble_str = "".join(part.serialize() for part in preamble_parts)

        # Build document body
        body_parts = self._generate_document_content()
        body_str = "".join(part.serialize() for part in body_parts)

        # Assemble complete document
        class_opts = f"[{','.join(self.class_options)}]" if self.class_options else ""
        return (
            f"\\documentclass{class_opts}{{{doc_class}}}\n"
            f"{preamble_str}"
            f"\\begin{{document}}\n"
            f"{body_str}\n"
            f"\\end{{document}}\n"
        )
