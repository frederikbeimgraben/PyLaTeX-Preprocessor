"""German ``\\crefname`` / ``\\Crefname`` declarations."""

from pytex import Crefname, TeX
from pytex_komascript.model import Block

#: ``(type, singular, plural)`` rows for ``\\crefname`` / ``\\Crefname``.
CREFNAMES: list[tuple[str, str, str]] = [
    ("figure", "Abbildung", "Abbildungen"),
    ("table", "Tabelle", "Tabellen"),
    ("equation", "Gleichung", "Gleichungen"),
    ("chapter", "Kapitel", "Kapitel"),
    ("section", "Abschnitt", "Abschnitte"),
    ("subsection", "Unterabschnitt", "Unterabschnitte"),
    ("subsubsection", "Unterunterabschnitt", "Unterunterabschnitte"),
    ("listing", "Listing", "Codeblock"),
    ("appendix", "Anhang", "Anhänge"),
    ("footnote", "Fußnote", "Fußnoten"),
    ("enumi", "Punkt", "Punkte"),
    ("page", "Seite", "Seiten"),
]


def cleveref_block() -> TeX:
    parts: list[TeX] = []
    for ty, sg, pl in CREFNAMES:
        parts.append(Crefname(ty, sg, pl, cap=False))
        parts.append(Crefname(ty, sg, pl, cap=True))
    return Block(*parts)


__all__ = ["CREFNAMES", "cleveref_block"]
