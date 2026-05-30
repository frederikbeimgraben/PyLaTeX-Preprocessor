"""Package collection and dependency/conflict resolution for documents."""

from collections.abc import Iterable
from dataclasses import dataclass, field
from typing import override

from ..model.base_model import Package, TeX


def collect_packages(node: TeX) -> set[Package | str]:
    """Recursively collect all required packages from a TeX tree."""
    packages = set(node.required_packages)
    for child in node.children:
        packages.update(collect_packages(child))
    return packages


def _to_package(item: Package | str) -> Package:
    return item if isinstance(item, Package) else Package(name=item)


def resolve_package_dependencies(packages: set[Package | str]) -> list[Package]:
    """Resolve package dependencies and return a load-ordered Package list.

    Strings are wrapped in option-less ``Package`` instances. Items with the
    same ``name`` deduplicate; if any duplicate carries an ``options`` string
    that version wins so options survive collection from multiple sources.
    The result is topologically sorted so a required package is emitted
    before any package that depends on it, with alphabetical ordering as the
    tie-break for independent packages.
    """
    by_name: dict[str, Package] = {}

    def merge(pkg: Package) -> None:
        existing = by_name.get(pkg.name)
        if existing is None or (existing.options is None and pkg.options is not None):
            by_name[pkg.name] = pkg

    for raw in packages:
        merge(_to_package(raw))

    # Pull in transitive requires.
    queue: list[Package] = list(by_name.values())
    while queue:
        pkg = queue.pop()
        for required in pkg.requires:
            req_pkg = _to_package(required)
            if req_pkg.name not in by_name:
                merge(req_pkg)
                queue.append(req_pkg)

    # Conflict detection
    for pkg in by_name.values():
        for conflict in pkg.conflicts:
            conflict_name = conflict if isinstance(conflict, str) else conflict.name
            if conflict_name in by_name:
                raise ValueError(
                    f"Package conflict: {pkg.name} conflicts with {conflict_name}"
                )

    ordered: list[Package] = []
    visited: set[str] = set()
    visiting: set[str] = set()

    def visit(name: str) -> None:
        if name in visited or name in visiting:
            return
        pkg = by_name.get(name)
        if pkg is None:
            return
        visiting.add(name)
        # Sort required names so independent deps stay alphabetically ordered.
        for req in sorted(
            r if isinstance(r, str) else r.name for r in pkg.requires
        ):
            visit(req)
        visiting.discard(name)
        visited.add(name)
        ordered.append(pkg)

    for name in sorted(by_name):
        visit(name)

    return ordered


def serialize_usepackage(pkg: Package) -> str:
    """Serialise ``\\usepackage[opts]{name}`` for a single Package."""
    if pkg.options:
        return f"\\usepackage[{pkg.options}]{{{pkg.name}}}"
    return f"\\usepackage{{{pkg.name}}}"


@dataclass(init=False)
class RequirePackages(TeX):
    """Anchor node: registers packages without emitting any TeX of its own.

    Use to pull in packages whose presence is implied by hand-written TeX
    inside a :class:`pytex.NewCommand` body or similar, where no other node
    in the tree declares the dependency. Auto-collection then surfaces them
    in the ``\\usepackage`` block at the top of the document.
    """

    _packages: frozenset[Package | str] = field(default_factory=frozenset)

    def __init__(self, *packages: Package | str) -> None:
        self._packages = frozenset(packages)

    @property
    @override
    def required_packages(self) -> set[Package | str]:
        return set(self._packages)

    @property
    @override
    def children(self) -> tuple[TeX, ...]:
        return ()

    @override
    def serialize(self) -> str:
        return ""


# Imported for re-export in module __all__ rebuild
_ = Iterable
