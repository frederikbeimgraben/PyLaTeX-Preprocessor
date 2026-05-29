"""Glossary and acronym support (the ``glossaries`` package).

Provides typed entries (:class:`GlossaryEntry`, :class:`AcronymEntry`),
containers (:class:`Glossary`, :class:`Acronyms`), the ``\\makeglossaries`` /
``\\printglossary`` controls, and reference helpers (:func:`gls`, :func:`glspl`,
:func:`acr`, :func:`acrlong`, :func:`acrfull`).
"""

from dataclasses import dataclass, field
from typing import Literal, override

from ..model.base_model import Package, TeX
from ..model.raw import Raw

#: Reference case forms.
type Case = Literal["lower", "upper", "capitalized"]
#: Reference format forms.
type Format = Literal["short", "long", "full", "name", "text"]

_GLOSSARIES = "glossaries"


def _text(value: TeX | str) -> TeX:
    """Coerce prose fields without turning spaces into ``~``."""
    return Raw(value, escape_spaces=False) if isinstance(value, str) else value


@dataclass(init=False)
class GlossaryEntry(TeX):
    """``\\newglossaryentry{key}{name=...,description=...,...}``."""

    key: str
    name: TeX
    description: TeX
    plural: TeX | None
    symbol: TeX | None
    first: TeX | None
    text: TeX | None
    genitive: TeX | None
    dative: TeX | None

    def __init__(
        self,
        key: str,
        name: TeX | str,
        description: TeX | str,
        *,
        plural: TeX | str | None = None,
        symbol: TeX | str | None = None,
        first: TeX | str | None = None,
        text: TeX | str | None = None,
        genitive: TeX | str | None = None,
        dative: TeX | str | None = None,
    ) -> None:
        self.key = key
        self.name = _text(name)
        self.description = _text(description)
        self.plural = _text(plural) if plural is not None else None
        self.symbol = _text(symbol) if symbol is not None else None
        self.first = _text(first) if first is not None else None
        self.text = _text(text) if text is not None else None
        self.genitive = _text(genitive) if genitive is not None else None
        self.dative = _text(dative) if dative is not None else None

    @property
    @override
    def required_packages(self) -> set[Package | str]:
        return {_GLOSSARIES}

    @property
    @override
    def children(self) -> tuple[TeX, ...]:
        return ()

    def _fields(self) -> list[tuple[str, TeX]]:
        fields: list[tuple[str, TeX]] = [
            ("name", self.name),
            ("description", self.description),
        ]
        for label, value in (
            ("plural", self.plural),
            ("symbol", self.symbol),
            ("first", self.first),
            ("text", self.text),
            ("genitive", self.genitive),
            ("dative", self.dative),
        ):
            if value is not None:
                fields.append((label, value))
        return fields

    @override
    def serialize(self) -> str:
        body = ",\n  ".join(f"{k}={{{v.serialize()}}}" for k, v in self._fields())
        return f"\\newglossaryentry{{{self.key}}}{{\n  {body}\n}}"


@dataclass(init=False)
class AcronymEntry(TeX):
    """``\\newacronym[description=...]{key}{short}{long}``."""

    key: str
    short: TeX
    long: TeX
    description: TeX | None
    plural: TeX | None

    def __init__(
        self,
        key: str,
        short: TeX | str,
        long: TeX | str,
        *,
        description: TeX | str | None = None,
        plural: TeX | str | None = None,
    ) -> None:
        self.key = key
        self.short = _text(short)
        self.long = _text(long)
        self.description = _text(description) if description is not None else None
        self.plural = _text(plural) if plural is not None else None

    @property
    @override
    def required_packages(self) -> set[Package | str]:
        return {_GLOSSARIES}

    @property
    @override
    def children(self) -> tuple[TeX, ...]:
        return ()

    @override
    def serialize(self) -> str:
        opts: list[str] = []
        if self.description is not None:
            opts.append(f"description={{{self.description.serialize()}}}")
        if self.plural is not None:
            opts.append(f"shortplural={{{self.plural.serialize()}}}")
        opt_str = f"[{','.join(opts)}]" if opts else ""
        return (
            f"\\newacronym{opt_str}{{{self.key}}}"
            f"{{{self.short.serialize()}}}{{{self.long.serialize()}}}"
        )


#: Either kind of glossary item.
type Entry = GlossaryEntry | AcronymEntry


@dataclass
class Glossary(TeX):
    """A collection of glossary / acronym definitions."""

    entries: tuple[Entry, ...] = field(default_factory=tuple)

    def __init__(self, *entries: Entry) -> None:
        self.entries = entries

    @property
    @override
    def required_packages(self) -> set[Package | str]:
        return {_GLOSSARIES}

    @property
    @override
    def children(self) -> tuple[TeX, ...]:
        return self.entries

    @override
    def serialize(self) -> str:
        return "\n".join(e.serialize() for e in self.entries)


class Acronyms(Glossary):
    """A collection of acronym definitions (a :class:`Glossary`)."""


# ---------------------------------------------------------------------------
# Controls
# ---------------------------------------------------------------------------


@dataclass
class _MakeGlossaries(TeX):
    @property
    @override
    def required_packages(self) -> set[Package | str]:
        return {_GLOSSARIES}

    @property
    @override
    def children(self) -> tuple[TeX, ...]:
        return ()

    @override
    def serialize(self) -> str:
        return "\\makeglossaries"


MakeGlossaries = _MakeGlossaries()


@dataclass
class PrintGlossary(TeX):
    """``\\printglossary[type=...,title=...]``."""

    type: str | None = None
    title: str | None = None

    @property
    @override
    def required_packages(self) -> set[Package | str]:
        return {_GLOSSARIES}

    @property
    @override
    def children(self) -> tuple[TeX, ...]:
        return ()

    @override
    def serialize(self) -> str:
        opts: list[str] = []
        if self.type is not None:
            opts.append(f"type={self.type}")
        if self.title is not None:
            opts.append(f"title={self.title}")
        opt_str = f"[{','.join(opts)}]" if opts else ""
        return f"\\printglossary{opt_str}"


# ---------------------------------------------------------------------------
# Reference helpers
# ---------------------------------------------------------------------------

_CASE_PREFIX: dict[Case, str] = {"lower": "gls", "upper": "GLS", "capitalized": "Gls"}


@dataclass
class _GlsRef(TeX):
    command: str
    key: str

    @property
    @override
    def required_packages(self) -> set[Package | str]:
        return {_GLOSSARIES}

    @property
    @override
    def children(self) -> tuple[TeX, ...]:
        return ()

    @override
    def serialize(self) -> str:
        return f"\\{self.command}{{{self.key}}}"


def _ref(stem: str, key: str, case: Case) -> _GlsRef:
    # \gls / \Gls / \GLS ; \glslong / \Glslong / \GLSlong ; etc.
    prefix = _CASE_PREFIX[case]
    command = prefix if not stem else f"{prefix}{stem}"
    return _GlsRef(command, key)


def gls(key: str, format: Format = "short", case: Case = "lower") -> _GlsRef:
    """Reference a glossary entry.

    ``format`` selects the displayed form (``short`` is the plain ``\\gls``;
    ``long``/``full`` map to long/full forms); ``case`` selects lower/upper/
    capitalized variants.
    """
    if format == "full":
        return acrfull(key, case)
    if format == "long":
        return _ref("long", key, case)
    if format in ("name", "text"):
        return _ref(format, key, case)
    return _ref("", key, case)


def glspl(key: str, format: Format = "short", case: Case = "lower") -> _GlsRef:
    """Plural reference (``\\glspl`` / ``\\Glspl`` / ``\\GLSpl``)."""
    if format == "long":
        return _ref("longpl", key, case)
    return _ref("pl", key, case)


def acr(key: str, case: Case = "lower") -> _GlsRef:
    """Acronym short form (``\\acrshort``)."""
    prefix = {"lower": "acrshort", "upper": "Acrshort", "capitalized": "Acrshort"}[case]
    return _GlsRef(prefix, key)


def acrlong(key: str, case: Case = "lower") -> _GlsRef:
    """Acronym long form (``\\acrlong``)."""
    prefix = {"lower": "acrlong", "upper": "Acrlong", "capitalized": "Acrlong"}[case]
    return _GlsRef(prefix, key)


def acrfull(key: str, case: Case = "lower") -> _GlsRef:
    """Acronym full form (``\\acrfull``)."""
    prefix = {"lower": "acrfull", "upper": "Acrfull", "capitalized": "Acrfull"}[case]
    return _GlsRef(prefix, key)


__all__ = [
    "GlossaryEntry",
    "AcronymEntry",
    "Glossary",
    "Acronyms",
    "MakeGlossaries",
    "PrintGlossary",
    "gls",
    "glspl",
    "acr",
    "acrlong",
    "acrfull",
]
