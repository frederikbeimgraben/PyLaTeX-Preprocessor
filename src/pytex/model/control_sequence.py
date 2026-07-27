from dataclasses import dataclass, field
from typing import Final, override

from ..helpers.parenting import attach
from ..interface.control_sequence import Parameters, ParameterType
from ..interface.package import PackageProtocol
from ..interface.tex import TeX
from ..registry import Registry
from .raw import Raw

__all__ = ["ControlSequence", "Parameter"]


@Registry.add
@dataclass(frozen=True, slots=True)
class Parameter[T: ParameterType = ParameterType](TeX):
    """One argument of a control sequence.

    A dict value renders as a comma-separated list of `key=value` pairs. That
    is the form of a LaTeX key-value option. A dict value has no child node.

    Attributes:
        optional: True renders the value inside `[...]`. False renders it
            inside `{...}`.
    """

    value: Final[T]
    optional: Final[bool] = False
    _parent: "TeX | None" = field(default=None, init=False, compare=False, repr=False)

    def __post_init__(self) -> None:
        attach(self, self.value)

    @property
    def _braces(self) -> tuple[str, str]:
        return ("[", "]") if self.optional else ("{", "}")

    @property
    @override
    def children(self) -> tuple[TeX]:
        if isinstance(self.value, dict):
            return tuple[TeX]()

        return (self.value if isinstance(self.value, TeX) else Raw(self.value),)

    @property
    @override
    def rendered(self) -> str:
        content: str | TeX = ""

        if isinstance(self.value, (TeX, str)):
            content = self.value
        else:
            content = ",".join(f"{key}={value}" for key, value in self.value.items())

        return f"{self._braces[0]}{content}{self._braces[1]}"


@Registry.add
@dataclass(frozen=True, slots=True)
class ControlSequence[P: Parameters](TeX):
    """A LaTeX control sequence and its parameters, for example `\\frac{a}{b}`.

    Attributes:
        name: The control sequence name without the leading backslash.
        required_packages: The package requirements of this node. The default
            is an empty set, so a control sequence requires no package until a
            caller names one.
    """

    name: Final[str]
    params: Final[P]
    required_packages: frozenset[PackageProtocol] = field(default_factory=frozenset)
    _parent: "TeX | None" = field(default=None, init=False, compare=False, repr=False)

    def __post_init__(self) -> None:
        if self.params is not None:
            attach(self, *self.params)

    @property
    @override
    def children(self) -> tuple[TeX, ...]:
        return tuple(self.params or ())

    @property
    @override
    def requires(self) -> frozenset[PackageProtocol]:
        return self.required_packages

    @property
    @override
    def rendered(self) -> str:
        body = "".join(p.rendered for p in (self.params or ()))
        return f"\\{self.name}{body}"
