"""German ``\\crefname`` / ``\\Crefname`` declarations."""

from pytex import Crefname, TeX
from pytex_komascript.model import Block

#: ``(type, singular, plural)`` rows for ``\\crefname`` / ``\\Crefname``.
CREFNAMES: tuple[tuple[str, str, str], ...] = (
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
)


def CleverefBlock() -> TeX:
    """All ``\\crefname`` / ``\\Crefname`` pairs as one Block."""
    return Block(
        *(
            Crefname(ty, sg, pl, cap=cap)
            for ty, sg, pl in CREFNAMES
            for cap in (False, True)
        )
    )


__all__ = ["CREFNAMES", "CleverefBlock"]
