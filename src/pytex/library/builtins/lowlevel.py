"""Low-level TeX/eTeX primitives and etoolbox hooks.

Strongly-typed wrappers for the bare-metal commands that show up in serious
preambles: ``\\def`` (with optional parameter text), ``\\let``, ``\\newtoks`` /
token-register assignment, ``\\immediate\\write``, register assignments
(``\\binoppenalty=10000``), etoolbox ``\\pretocmd`` / ``\\apptocmd`` /
``\\AtBeginEnvironment`` / ``\\AtEndEnvironment``, ifthen ``\\whiledo`` and the
fontspec ``\\IfFontExistsTF`` test.
"""

from dataclasses import dataclass
from typing import override

from ...model.base_model import Package, TeX
from ...model.raw import coerce_tex


def _coerce_body(value: TeX | str) -> TeX:
    """Coerce a macro body without escaping its inner spaces."""
    from ...model.raw import Raw

    if isinstance(value, TeX):
        return value
    return Raw(value, escape_spaces=False)


@dataclass(init=False)
class Def(TeX):
    """``\\def\\name<param-text>{body}`` — TeX primitive definition.

    ``param_text`` is the verbatim parameter text (``"#1#2"``, ``"=\\true"``,
    ...). ``global_`` switches to ``\\gdef``.
    """

    name: str
    body: TeX
    param_text: str
    global_: bool

    def __init__(
        self,
        name: str,
        body: TeX | str,
        *,
        param_text: str = "",
        global_: bool = False,
    ) -> None:
        self.name = name
        self.body = _coerce_body(body)
        self.param_text = param_text
        self.global_ = global_

    @property
    @override
    def children(self) -> tuple[TeX, ...]:
        return (self.body,)

    @override
    def serialize(self) -> str:
        cmd = "gdef" if self.global_ else "def"
        return f"\\{cmd}\\{self.name}{self.param_text}{{{self.body.serialize()}}}"


@dataclass
class Let(TeX):
    """``\\let\\target=\\source`` — alias one macro to another."""

    target: str
    source: str

    @property
    @override
    def children(self) -> tuple[TeX, ...]:
        return ()

    @override
    def serialize(self) -> str:
        return f"\\let\\{self.target}=\\{self.source}"


@dataclass
class NewToks(TeX):
    """``\\newtoks\\name`` — allocate a token register."""

    name: str

    @property
    @override
    def children(self) -> tuple[TeX, ...]:
        return ()

    @override
    def serialize(self) -> str:
        return f"\\newtoks\\{self.name}"


@dataclass(init=False)
class AssignToks(TeX):
    """``\\name={body}`` — assign a balanced token list to a token register.

    Set ``expand_after=True`` to emit
    ``\\name=\\expandafter{\\the\\name body}`` (the canonical
    "append to a toks register" idiom).
    """

    name: str
    body: TeX
    expand_after: bool

    def __init__(
        self,
        name: str,
        body: TeX | str,
        *,
        expand_after: bool = False,
    ) -> None:
        self.name = name
        self.body = _coerce_body(body)
        self.expand_after = expand_after

    @property
    @override
    def children(self) -> tuple[TeX, ...]:
        return (self.body,)

    @override
    def serialize(self) -> str:
        if self.expand_after:
            return (
                f"\\{self.name}=\\expandafter"
                f"{{\\the\\{self.name} {self.body.serialize()}}}"
            )
        return f"\\{self.name}={{{self.body.serialize()}}}"


@dataclass(init=False)
class ImmediateWrite(TeX):
    """``\\immediate\\write<stream>{body}`` — write to an output stream."""

    stream: str
    body: TeX

    def __init__(self, stream: str, body: TeX | str) -> None:
        self.stream = stream
        self.body = _coerce_body(body)

    @property
    @override
    def children(self) -> tuple[TeX, ...]:
        return (self.body,)

    @override
    def serialize(self) -> str:
        return f"\\immediate\\write\\{self.stream}{{{self.body.serialize()}}}"


@dataclass
class RegisterAssign(TeX):
    """``\\name=value`` — assign a length / counter / penalty register.

    Use for ``\\binoppenalty=10000``, ``\\@beginparpenalty=10000``,
    ``\\parfillskip=0pt plus 1fil``, ``\\spaceskip=...``, ``\\tolerance=...``.
    """

    name: str
    value: str | int

    @property
    @override
    def children(self) -> tuple[TeX, ...]:
        return ()

    @override
    def serialize(self) -> str:
        return f"\\{self.name}={self.value}"


_ETOOLBOX: frozenset[Package | str] = frozenset({"etoolbox"})


@dataclass(init=False)
class _PatchCmd(TeX):
    """Shared ``\\pretocmd`` / ``\\apptocmd`` body."""

    CMD: str = ""
    target: str
    patch: TeX
    success: TeX
    failure: TeX

    def __init__(
        self,
        target: str,
        patch: TeX | str,
        success: TeX | str = "",
        failure: TeX | str = "",
    ) -> None:
        self.target = target
        self.patch = _coerce_body(patch)
        self.success = _coerce_body(success)
        self.failure = _coerce_body(failure)

    @property
    @override
    def required_packages(self) -> set[Package | str]:
        return set(_ETOOLBOX)

    @property
    @override
    def children(self) -> tuple[TeX, ...]:
        return (self.patch, self.success, self.failure)

    @override
    def serialize(self) -> str:
        return (
            f"\\{self.CMD}{{\\{self.target}}}"
            f"{{{self.patch.serialize()}}}"
            f"{{{self.success.serialize()}}}"
            f"{{{self.failure.serialize()}}}"
        )


class Pretocmd(_PatchCmd):
    """``\\pretocmd{\\target}{patch}{success}{failure}`` (etoolbox)."""

    CMD = "pretocmd"


class Apptocmd(_PatchCmd):
    """``\\apptocmd{\\target}{patch}{success}{failure}`` (etoolbox)."""

    CMD = "apptocmd"


@dataclass(init=False)
class _EnvHook(TeX):
    """Shared ``\\AtBeginEnvironment`` / ``\\AtEndEnvironment``."""

    CMD: str = ""
    env: str
    body: TeX

    def __init__(self, env: str, body: TeX | str) -> None:
        self.env = env
        self.body = _coerce_body(body)

    @property
    @override
    def required_packages(self) -> set[Package | str]:
        return set(_ETOOLBOX)

    @property
    @override
    def children(self) -> tuple[TeX, ...]:
        return (self.body,)

    @override
    def serialize(self) -> str:
        return f"\\{self.CMD}{{{self.env}}}{{{self.body.serialize()}}}"


class AtBeginEnvironment(_EnvHook):
    """``\\AtBeginEnvironment{name}{body}`` (etoolbox)."""

    CMD = "AtBeginEnvironment"


class AtEndEnvironment(_EnvHook):
    """``\\AtEndEnvironment{name}{body}`` (etoolbox)."""

    CMD = "AtEndEnvironment"


@dataclass(init=False)
class Whiledo(TeX):
    """``\\whiledo{test}{body}`` (ifthen)."""

    test: str
    body: TeX

    def __init__(self, test: str, body: TeX | str) -> None:
        self.test = test
        self.body = _coerce_body(body)

    @property
    @override
    def required_packages(self) -> set[Package | str]:
        return {"ifthen"}

    @property
    @override
    def children(self) -> tuple[TeX, ...]:
        return (self.body,)

    @override
    def serialize(self) -> str:
        return f"\\whiledo{{{self.test}}}{{{self.body.serialize()}}}"


@dataclass(init=False)
class IfFontExistsTF(TeX):
    """``\\IfFontExistsTF{font}{true}{false}`` (fontspec)."""

    font: str
    true: TeX
    false: TeX

    def __init__(self, font: str, true: TeX | str, false: TeX | str) -> None:
        self.font = font
        self.true = _coerce_body(true)
        self.false = _coerce_body(false)

    @property
    @override
    def required_packages(self) -> set[Package | str]:
        return {"fontspec"}

    @property
    @override
    def children(self) -> tuple[TeX, ...]:
        return (self.true, self.false)

    @override
    def serialize(self) -> str:
        return (
            f"\\IfFontExistsTF{{{self.font}}}"
            f"{{{self.true.serialize()}}}"
            f"{{{self.false.serialize()}}}"
        )


@dataclass(init=False)
class IfUndefined(TeX):
    """``\\@ifundefined{name}{true}{false}``.

    Uses the @-letter variant; wrap in :class:`MakeAtLetter` if outside a
    package context.
    """

    name: str
    true: TeX
    false: TeX

    def __init__(self, name: str, true: TeX | str = "", false: TeX | str = "") -> None:
        self.name = name
        self.true = _coerce_body(true)
        self.false = _coerce_body(false)

    @property
    @override
    def children(self) -> tuple[TeX, ...]:
        return (self.true, self.false)

    @override
    def serialize(self) -> str:
        return (
            f"\\@ifundefined{{{self.name}}}"
            f"{{{self.true.serialize()}}}{{{self.false.serialize()}}}"
        )


@dataclass(init=False)
class Ifnum(TeX):
    """``\\ifnum <test>\\relax body\\fi`` — primitive numeric test.

    ``test`` is the verbatim left-hand side (e.g. ``"\\value{chapter}>0"``).
    The ``\\relax`` after the test stops TeX from scanning further digits
    into the comparison.
    """

    test: str
    body: TeX
    else_body: TeX | None

    def __init__(
        self,
        test: str,
        body: TeX | str,
        *,
        else_body: TeX | str | None = None,
    ) -> None:
        self.test = test
        self.body = _coerce_body(body)
        self.else_body = _coerce_body(else_body) if else_body is not None else None

    @property
    @override
    def children(self) -> tuple[TeX, ...]:
        if self.else_body is None:
            return (self.body,)
        return (self.body, self.else_body)

    @override
    def serialize(self) -> str:
        head = f"\\ifnum {self.test}\\relax {self.body.serialize()}"
        if self.else_body is None:
            return f"{head}\\fi"
        return f"{head}\\else {self.else_body.serialize()}\\fi"


@dataclass(init=False)
class Ifdefstring(TeX):
    """``\\ifdefstring{\\name}{string}{true}{false}`` (etoolbox)."""

    name: str
    value: str
    true: TeX
    false: TeX

    def __init__(
        self,
        name: str,
        value: str,
        true: TeX | str,
        false: TeX | str,
    ) -> None:
        self.name = name
        self.value = value
        self.true = _coerce_body(true)
        self.false = _coerce_body(false)

    @property
    @override
    def required_packages(self) -> set[Package | str]:
        return set(_ETOOLBOX)

    @property
    @override
    def children(self) -> tuple[TeX, ...]:
        return (self.true, self.false)

    @override
    def serialize(self) -> str:
        return (
            f"\\ifdefstring{{\\{self.name}}}{{{self.value}}}"
            f"{{{self.true.serialize()}}}{{{self.false.serialize()}}}"
        )


@dataclass(init=False)
class BeginAccSupp(TeX):
    """``\\BeginAccSupp{ActualText=...} body \\EndAccSupp{}`` wrapper (accsupp)."""

    actual_text: str
    body: TeX

    def __init__(self, body: TeX | str, *, actual_text: str = "") -> None:
        self.actual_text = actual_text
        self.body = _coerce_body(body)

    @property
    @override
    def required_packages(self) -> set[Package | str]:
        return {"accsupp"}

    @property
    @override
    def children(self) -> tuple[TeX, ...]:
        return (self.body,)

    @override
    def serialize(self) -> str:
        return (
            f"\\BeginAccSupp{{ActualText={self.actual_text}}}"
            f"{self.body.serialize()}\\EndAccSupp{{}}"
        )


__all__ = [
    "Def",
    "Let",
    "NewToks",
    "AssignToks",
    "ImmediateWrite",
    "RegisterAssign",
    "Pretocmd",
    "Apptocmd",
    "AtBeginEnvironment",
    "AtEndEnvironment",
    "Whiledo",
    "IfFontExistsTF",
    "IfUndefined",
    "Ifnum",
    "Ifdefstring",
    "BeginAccSupp",
]
