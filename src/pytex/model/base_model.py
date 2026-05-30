from dataclasses import dataclass, field
from typing import Protocol, override, runtime_checkable


@dataclass(eq=False, frozen=True)
class Package:
    """A LaTeX package, optionally with a comma-separated options string.

    Equality and hashing are by ``name`` so a set deduplicates two
    ``Package`` instances with the same name even if their ``options``
    differ; callers should not rely on which one survives. Strings compare
    equal to a ``Package`` with the same ``name`` for backwards compatibility
    with set-of-(Package|str).
    """

    name: str
    options: str | None = None
    conflicts: frozenset["Package | str"] = field(default_factory=frozenset)
    requires: frozenset["Package | str"] = field(default_factory=frozenset)
    before: frozenset["Package | str"] = field(default_factory=frozenset)
    after: frozenset["Package | str"] = field(default_factory=frozenset)

    @override
    def __hash__(self) -> int:
        return hash(self.name)

    @override
    def __eq__(self, other: object) -> bool:
        if isinstance(other, Package):
            return self.name == other.name
        if isinstance(other, str):
            return self.name == other
        return NotImplemented

    def with_options(self, options: str) -> "Package":
        return Package(
            name=self.name,
            options=options,
            conflicts=self.conflicts,
            requires=self.requires,
            before=self.before,
            after=self.after,
        )


@runtime_checkable
class TeX(Protocol):
    @property
    def required_packages(self) -> set[Package | str]:
        return set()

    @property
    def children(self) -> tuple["TeX", ...]: ...

    def serialize(self) -> str: ...
