"""Source-code listings (the ``listings`` package).

A generic :class:`Listing` plus per-language constructors (:func:`Python`,
:func:`JavaScript`, ...) and the ``\\lstset`` / ``\\lstdefinestyle`` /
``\\lstinline`` helpers.
"""

from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import override

from ..model.base_model import Package, TeX

_LISTINGS = "listings"


def _render_options(options: Mapping[str, object]) -> str:
    parts: list[str] = []
    for key, value in options.items():
        if value is True:
            parts.append(key)
        elif value is False:
            continue
        else:
            parts.append(f"{key}={{{value}}}")
    return ",".join(parts)


@dataclass(init=False)
class Listing(TeX):
    """``\\begin{lstlisting}[opts] CODE \\end{lstlisting}``.

    ``code`` is emitted verbatim. ``language``/``caption``/``label``/``style``
    are convenience options; arbitrary extra options go in ``options``.
    """

    code: str
    language: str | None
    caption: str | None
    label: str | None
    style: str | None
    options: dict[str, object]

    def __init__(
        self,
        code: str,
        *,
        language: str | None = None,
        caption: str | None = None,
        label: str | None = None,
        style: str | None = None,
        options: Mapping[str, object] | None = None,
    ) -> None:
        self.code = code
        self.language = language
        self.caption = caption
        self.label = label
        self.style = style
        self.options = dict(options) if options else {}

    @property
    @override
    def required_packages(self) -> set[Package | str]:
        return {_LISTINGS}

    @property
    @override
    def children(self) -> tuple[TeX, ...]:
        return ()

    def _all_options(self) -> dict[str, object]:
        merged: dict[str, object] = {}
        if self.language is not None:
            merged["language"] = self.language
        if self.style is not None:
            merged["style"] = self.style
        if self.caption is not None:
            merged["caption"] = self.caption
        if self.label is not None:
            merged["label"] = self.label
        merged.update(self.options)
        return merged

    @override
    def serialize(self) -> str:
        rendered = _render_options(self._all_options())
        opt_str = f"[{rendered}]" if rendered else ""
        code = self.code.strip("\n")
        return f"\\begin{{lstlisting}}{opt_str}\n{code}\n\\end{{lstlisting}}"


@dataclass(init=False)
class LstSet(TeX):
    """``\\lstset{key=value,...}``."""

    options: dict[str, object]

    def __init__(self, options: Mapping[str, object] | None = None, **kwargs: object) -> None:
        self.options = {**(dict(options) if options else {}), **kwargs}

    @property
    @override
    def required_packages(self) -> set[Package | str]:
        return {_LISTINGS}

    @property
    @override
    def children(self) -> tuple[TeX, ...]:
        return ()

    @override
    def serialize(self) -> str:
        return f"\\lstset{{{_render_options(self.options)}}}"


@dataclass(init=False)
class LstDefineStyle(TeX):
    """``\\lstdefinestyle{name}{key=value,...}``."""

    name: str
    options: dict[str, object]

    def __init__(
        self, name: str, options: Mapping[str, object] | None = None, **kwargs: object
    ) -> None:
        self.name = name
        self.options = {**(dict(options) if options else {}), **kwargs}

    @property
    @override
    def required_packages(self) -> set[Package | str]:
        return {_LISTINGS}

    @property
    @override
    def children(self) -> tuple[TeX, ...]:
        return ()

    @override
    def serialize(self) -> str:
        return f"\\lstdefinestyle{{{self.name}}}{{{_render_options(self.options)}}}"


@dataclass
class InlineCode(TeX):
    """``\\lstinline[language=...]|code|`` inline listing."""

    code: str
    language: str | None = None
    _delim: str = field(default="|", compare=False)

    @property
    @override
    def required_packages(self) -> set[Package | str]:
        return {_LISTINGS}

    @property
    @override
    def children(self) -> tuple[TeX, ...]:
        return ()

    @override
    def serialize(self) -> str:
        delim = self._delim if self._delim not in self.code else "!"
        opt = f"[language={self.language}]" if self.language else ""
        return f"\\lstinline{opt}{delim}{self.code}{delim}"


#: Maps a friendly constructor name to the ``listings`` language token.
LANGUAGES: dict[str, str] = {
    "Python": "Python",
    "JavaScript": "JavaScript",
    "TypeScript": "JavaScript",
    "Cpp": "C++",
    "C": "C",
    "Java": "Java",
    "Shell": "bash",
    "Bash": "bash",
    "Sql": "SQL",
    "Html": "HTML",
    "Php": "PHP",
    "Rust": "Rust",
    "Json": "",
    "LaTeXListing": "TeX",
}


def _make_language(token: str):
    def constructor(
        code: str,
        *,
        caption: str | None = None,
        label: str | None = None,
        style: str | None = None,
        options: Mapping[str, object] | None = None,
    ) -> Listing:
        return Listing(
            code,
            language=token or None,
            caption=caption,
            label=label,
            style=style,
            options=options,
        )

    return constructor


# Generate per-language constructors into the module namespace.
Python = _make_language(LANGUAGES["Python"])
JavaScript = _make_language(LANGUAGES["JavaScript"])
TypeScript = _make_language(LANGUAGES["TypeScript"])
Cpp = _make_language(LANGUAGES["Cpp"])
C = _make_language(LANGUAGES["C"])
Java = _make_language(LANGUAGES["Java"])
Shell = _make_language(LANGUAGES["Shell"])
Bash = _make_language(LANGUAGES["Bash"])
Sql = _make_language(LANGUAGES["Sql"])
Html = _make_language(LANGUAGES["Html"])
Php = _make_language(LANGUAGES["Php"])
Rust = _make_language(LANGUAGES["Rust"])
Json = _make_language(LANGUAGES["Json"])
LaTeXListing = _make_language(LANGUAGES["LaTeXListing"])


__all__ = [
    "Listing",
    "LstSet",
    "LstDefineStyle",
    "InlineCode",
    "LANGUAGES",
    "Python",
    "JavaScript",
    "TypeScript",
    "Cpp",
    "C",
    "Java",
    "Shell",
    "Bash",
    "Sql",
    "Html",
    "Php",
    "Rust",
    "Json",
    "LaTeXListing",
]
