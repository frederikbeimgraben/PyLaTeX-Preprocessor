"""Generic native LaTeX preamble/runtime commands.

Provides strongly-typed wrappers for the small primitives that are needed
to build complex preambles in pure Python instead of raw TeX strings:
``\\newcommand`` / ``\\renewcommand`` / ``\\providecommand``,
``\\DeclareRobustCommand``, ``\\newlength`` / ``\\setlength``,
``\\newcounter`` / ``\\setcounter`` / ``\\addtocounter``,
``\\counterwithin`` / ``\\counterwithout``, ``\\AtBeginDocument`` /
``\\AtEndDocument``, ``\\hypersetup``, ``\\crefname`` / ``\\Crefname``,
``\\renewenvironment`` / ``\\newenvironment`` and a generic ``Command`` for
"name + bracketed-option + braced-args" macros not worth a dedicated class.
"""

from collections.abc import Iterable
from dataclasses import dataclass
from typing import ClassVar, override

from ...model.base_model import Package, TeX
from ...model.raw import Raw, coerce_tex


def _coerce_body(value: TeX | str) -> TeX:
    """Coerce a command body to TeX without space-escaping it.

    Macro / environment bodies are TeX source — internal spaces must survive
    as actual spaces, not as ``~`` ties.
    """
    if isinstance(value, TeX):
        return value
    return Raw(value, escape_spaces=False)


@dataclass(init=False)
class Command(TeX):
    """Generic ``\\name[opts]{arg1}{arg2}...`` command.

    Use directly when no dedicated class exists; otherwise prefer subclasses.
    """

    name: str
    args: tuple[TeX, ...]
    options: str | None
    _requires: frozenset[Package | str]

    def __init__(
        self,
        name: str,
        *args: TeX | str,
        options: str | None = None,
        requires: "Iterable[Package | str] | None" = None,
    ) -> None:
        self.name = name
        self.args = tuple(coerce_tex(a) for a in args)
        self.options = options
        self._requires = frozenset(requires or ())

    @property
    @override
    def required_packages(self) -> set[Package | str]:
        return set(self._requires)

    @property
    @override
    def children(self) -> tuple[TeX, ...]:
        return self.args

    @override
    def serialize(self) -> str:
        opt = f"[{self.options}]" if self.options is not None else ""
        body = "".join(f"{{{a.serialize()}}}" for a in self.args)
        return f"\\{self.name}{opt}{body}"


@dataclass(init=False)
class _DefBase(TeX):
    """Shared logic for ``\\newcommand`` / ``\\renewcommand`` /
    ``\\providecommand`` / ``\\DeclareRobustCommand``.
    """

    CMD: ClassVar[str] = ""

    name: str
    body: TeX
    n_args: int
    default: str | None

    def __init__(
        self,
        name: str,
        body: TeX | str,
        *,
        n_args: int = 0,
        default: str | None = None,
    ) -> None:
        self.name = name
        self.body = _coerce_body(body)
        self.n_args = n_args
        self.default = default

    @property
    @override
    def children(self) -> tuple[TeX, ...]:
        return (self.body,)

    @override
    def serialize(self) -> str:
        head = f"\\{self.CMD}{{\\{self.name}}}"
        if self.n_args:
            head += f"[{self.n_args}]"
        if self.default is not None:
            head += f"[{self.default}]"
        return f"{head}{{{self.body.serialize()}}}"


class NewCommand(_DefBase):
    """``\\newcommand{\\name}[n][default]{body}``."""

    CMD: ClassVar[str] = "newcommand"


class RenewCommand(_DefBase):
    """``\\renewcommand{\\name}[n][default]{body}``."""

    CMD: ClassVar[str] = "renewcommand"


class ProvideCommand(_DefBase):
    """``\\providecommand{\\name}[n][default]{body}``."""

    CMD: ClassVar[str] = "providecommand"


class DeclareRobustCommand(_DefBase):
    """``\\DeclareRobustCommand{\\name}[n][default]{body}``."""

    CMD: ClassVar[str] = "DeclareRobustCommand"


@dataclass
class NewLength(TeX):
    """``\\newlength{\\name}``."""

    name: str

    @property
    @override
    def children(self) -> tuple[TeX, ...]:
        return ()

    @override
    def serialize(self) -> str:
        return f"\\newlength{{\\{self.name}}}"


@dataclass
class SetLength(TeX):
    """``\\setlength{\\name}{value}``."""

    name: str
    value: str

    @property
    @override
    def children(self) -> tuple[TeX, ...]:
        return ()

    @override
    def serialize(self) -> str:
        return f"\\setlength{{\\{self.name}}}{{{self.value}}}"


@dataclass
class NewCounter(TeX):
    """``\\newcounter{name}``."""

    name: str

    @property
    @override
    def children(self) -> tuple[TeX, ...]:
        return ()

    @override
    def serialize(self) -> str:
        return f"\\newcounter{{{self.name}}}"


@dataclass
class SetCounter(TeX):
    """``\\setcounter{name}{value}``."""

    name: str
    value: str | int

    @property
    @override
    def children(self) -> tuple[TeX, ...]:
        return ()

    @override
    def serialize(self) -> str:
        return f"\\setcounter{{{self.name}}}{{{self.value}}}"


@dataclass
class CounterWithin(TeX):
    """``\\counterwithin{child}{parent}`` (chngcntr / KOMA)."""

    child: str
    parent: str
    star: bool = False

    @property
    @override
    def required_packages(self) -> set[Package | str]:
        return {"chngcntr"}

    @property
    @override
    def children(self) -> tuple[TeX, ...]:
        return ()

    @override
    def serialize(self) -> str:
        star = "*" if self.star else ""
        return f"\\counterwithin{star}{{{self.child}}}{{{self.parent}}}"


@dataclass
class CounterWithout(TeX):
    """``\\counterwithout{child}{parent}``."""

    child: str
    parent: str
    star: bool = False

    @property
    @override
    def required_packages(self) -> set[Package | str]:
        return {"chngcntr"}

    @property
    @override
    def children(self) -> tuple[TeX, ...]:
        return ()

    @override
    def serialize(self) -> str:
        star = "*" if self.star else ""
        return f"\\counterwithout{star}{{{self.child}}}{{{self.parent}}}"


@dataclass(init=False)
class AtBeginDocument(TeX):
    """``\\AtBeginDocument{body}``."""

    body: TeX

    def __init__(self, body: TeX | str) -> None:
        self.body = coerce_tex(body)

    @property
    @override
    def children(self) -> tuple[TeX, ...]:
        return (self.body,)

    @override
    def serialize(self) -> str:
        return f"\\AtBeginDocument{{{self.body.serialize()}}}"


@dataclass(init=False)
class AtEndDocument(TeX):
    """``\\AtEndDocument{body}``."""

    body: TeX

    def __init__(self, body: TeX | str) -> None:
        self.body = coerce_tex(body)

    @property
    @override
    def children(self) -> tuple[TeX, ...]:
        return (self.body,)

    @override
    def serialize(self) -> str:
        return f"\\AtEndDocument{{{self.body.serialize()}}}"


@dataclass(init=False)
class MakeAtLetter(TeX):
    """``\\makeatletter ... \\makeatother`` wrapper for ``@``-letter code."""

    body: TeX

    def __init__(self, body: TeX | str) -> None:
        self.body = coerce_tex(body)

    @property
    @override
    def children(self) -> tuple[TeX, ...]:
        return (self.body,)

    @override
    def serialize(self) -> str:
        return f"\\makeatletter\n{self.body.serialize()}\n\\makeatother"


@dataclass
class Hypersetup(TeX):
    """``\\hypersetup{key=value,...}``."""

    options: str

    @property
    @override
    def required_packages(self) -> set[Package | str]:
        return {"hyperref"}

    @property
    @override
    def children(self) -> tuple[TeX, ...]:
        return ()

    @override
    def serialize(self) -> str:
        return f"\\hypersetup{{{self.options}}}"


@dataclass
class Crefname(TeX):
    """``\\crefname{type}{singular}{plural}`` (lowercase variant)."""

    type: str
    singular: str
    plural: str
    cap: bool = False

    @property
    @override
    def required_packages(self) -> set[Package | str]:
        return {"cleveref"}

    @property
    @override
    def children(self) -> tuple[TeX, ...]:
        return ()

    @override
    def serialize(self) -> str:
        cmd = "Crefname" if self.cap else "crefname"
        return f"\\{cmd}{{{self.type}}}{{{self.singular}}}{{{self.plural}}}"


@dataclass(init=False)
class NewEnvironment(TeX):
    """``\\newenvironment{name}[n][default]{begin}{end}``.

    ``renew=True`` switches to ``\\renewenvironment``.
    """

    name: str
    begin: TeX
    end: TeX
    n_args: int
    default: str | None
    renew: bool

    def __init__(
        self,
        name: str,
        begin: TeX | str,
        end: TeX | str,
        *,
        n_args: int = 0,
        default: str | None = None,
        renew: bool = False,
    ) -> None:
        self.name = name
        self.begin = _coerce_body(begin)
        self.end = _coerce_body(end)
        self.n_args = n_args
        self.default = default
        self.renew = renew

    @property
    @override
    def children(self) -> tuple[TeX, ...]:
        return (self.begin, self.end)

    @override
    def serialize(self) -> str:
        cmd = "renewenvironment" if self.renew else "newenvironment"
        head = f"\\{cmd}{{{self.name}}}"
        if self.n_args:
            head += f"[{self.n_args}]"
        if self.default is not None:
            head += f"[{self.default}]"
        return f"{head}{{{self.begin.serialize()}}}{{{self.end.serialize()}}}"


@dataclass
class GlobalDef(TeX):
    """``\\gdef\\name{body}`` — primitive global definition."""

    name: str
    body: str

    @property
    @override
    def children(self) -> tuple[TeX, ...]:
        return ()

    @override
    def serialize(self) -> str:
        return f"\\gdef\\{self.name}{{{self.body}}}"


__all__ = [
    "Command",
    "NewCommand",
    "RenewCommand",
    "ProvideCommand",
    "DeclareRobustCommand",
    "NewLength",
    "SetLength",
    "NewCounter",
    "SetCounter",
    "CounterWithin",
    "CounterWithout",
    "AtBeginDocument",
    "AtEndDocument",
    "MakeAtLetter",
    "Hypersetup",
    "Crefname",
    "NewEnvironment",
    "GlobalDef",
]
