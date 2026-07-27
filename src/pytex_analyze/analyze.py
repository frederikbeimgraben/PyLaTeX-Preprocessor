"""The static checks that the analysis pass runs over a `TeX` node tree."""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from enum import Enum
from typing import TYPE_CHECKING, cast

from pytex.model.control_sequence import ControlSequence, Parameter
from pytex.model.image import IncludeImage
from pytex.model.raw import Raw

if TYPE_CHECKING:
    from collections.abc import Iterator

    from pytex.interface.control_sequence import Parameters
    from pytex.interface.tex import TeX

__all__ = ["Issue", "Severity", "analyze"]

# Control sequences that point to a label by name. Each one takes a single
# argument. That argument can hold more than one label name, separated by
# commas.
_REF_COMMANDS = frozenset(
    {"ref", "pageref", "nameref", "autoref", "eqref", "vref", "cref", "Cref"}
)
_LABEL_COMMANDS = frozenset({"label"})


class Severity(Enum):
    WARNING = "warning"
    ERROR = "error"


@dataclass(frozen=True)
class Issue:
    severity: Severity
    message: str


def _walk(node: TeX) -> Iterator[TeX]:
    yield node
    for child in node.children or ():
        yield from _walk(child)


def _first_required_text(cs: ControlSequence[Parameters]) -> str | None:
    """Return the text of the first required parameter of `cs`.

    Returns:
        The parameter text. The result is `None` when `cs` has no required
        parameter, or when the first required parameter is neither a string
        nor a `Raw` node.
    """
    for param in cs.params or ():
        if isinstance(param, Parameter) and not param.optional:
            value = param.value
            if isinstance(value, str):
                return value
            if isinstance(value, Raw):
                return value.content
            return None
    return None


def analyze(node: TeX) -> list[Issue]:
    """Return the problems found in the node tree at `node`.

    The pass reads `node` and every child node below it. It changes nothing.
    For an image it also checks whether the source file exists on disk.

    The checks see a label or a reference only in a `ControlSequence` node.
    A `\\label` inside a `Raw` string stays invisible. The optimize pass
    converts a `Raw` that holds only that one control sequence. It leaves a
    `\\label` inside a longer `Raw` string as text.

    Returns:
        The issues in this order: missing image files in node-tree order,
        then duplicate labels by name, then undefined references by name.
    """
    label_counts: Counter[str] = Counter()
    references: list[str] = []
    issues: list[Issue] = []

    for current in _walk(node):
        if isinstance(current, ControlSequence):
            cs = cast("ControlSequence[Parameters]", current)
            if (
                cs.name in _LABEL_COMMANDS
                and (text := _first_required_text(cs)) is not None
            ):
                label_counts[text] += 1
            elif (
                cs.name in _REF_COMMANDS
                and (text := _first_required_text(cs)) is not None
            ):
                references.extend(
                    name.strip() for name in text.split(",") if name.strip()
                )
        elif isinstance(current, IncludeImage) and not current.source_path.exists():
            issues.append(
                Issue(
                    Severity.ERROR,
                    f"image file not found: {current.source_path}",
                )
            )

    for label, count in sorted(label_counts.items()):
        if count > 1:
            issues.append(
                Issue(Severity.WARNING, f"label {label!r} defined {count} times")
            )

    defined = set(label_counts)
    for name in sorted(set(references)):
        if name not in defined:
            issues.append(
                Issue(Severity.WARNING, f"reference to undefined label {name!r}")
            )

    return issues
