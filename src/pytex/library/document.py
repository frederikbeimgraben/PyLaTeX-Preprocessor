"""High-level Document abstraction for LaTeX.

Provides the Document class that handles document structure, package management,
metadata (title, author, date), and automatic preamble generation.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import override

from ..model.base_model import Package, TeX
from ..model.raw import Raw


def _collect_packages(
    node: TeX, seen: set[Package | str] | None = None
) -> set[Package | str]:
    """Recursively collect all required packages from a TeX tree.

    Args:
        node: Root of the TeX tree to scan
        seen: Set of already-seen packages (for cycle detection)

    Returns:
        Set of all packages required by the tree
    """
    if seen is None:
        seen = set()

    packages = set(node.required_packages)

    # Recursively collect from children
    for child in node.children:
        packages.update(_collect_packages(child, seen))

    return packages


def _resolve_package_dependencies(packages: set[Package | str]) -> set[str]:
    """Resolve package dependencies and return final set of package names.

    Args:
        packages: Set of packages (Package objects or strings)

    Returns:
        Set of package name strings with dependencies resolved

    Raises:
        ValueError: If package conflicts are detected
    """
    result: set[str] = set()
    package_objects: dict[str, Package] = {}

    # Separate Package objects from strings
    for pkg in packages:
        if isinstance(pkg, Package):
            package_objects[pkg.name] = pkg
            result.add(pkg.name)
        else:
            result.add(pkg)

    # Check for conflicts
    for pkg_obj in package_objects.values():
        for conflict in pkg_obj.conflicts:
            conflict_name = conflict if isinstance(conflict, str) else conflict.name
            if conflict_name in result:
                raise ValueError(
                    f"Package conflict: {pkg_obj.name} conflicts with {conflict_name}"
                )

    # Add required dependencies
    for pkg_obj in package_objects.values():
        for required in pkg_obj.requires:
            required_name = required if isinstance(required, str) else required.name
            result.add(required_name)

    return result


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
            packages={"amsmath", "graphicx"}
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

        # Collect all packages (from explicit list + from content tree)
        all_packages = set(self.packages)
        all_packages.update(_collect_packages(self.content))
        if self.preamble:
            all_packages.update(_collect_packages(self.preamble))

        # Resolve dependencies and conflicts
        resolved_packages = _resolve_package_dependencies(all_packages)

        # Generate \usepackage commands
        for pkg_name in sorted(resolved_packages):
            preamble_parts.append(
                Raw(f"\\usepackage{{{pkg_name}}}\n", escape_spaces=False, safe=False)
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
        return (
            f"\\documentclass{{{doc_class}}}\n"
            f"{preamble_str}"
            f"\\begin{{document}}\n"
            f"{body_str}\n"
            f"\\end{{document}}\n"
        )
