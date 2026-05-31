from typing import Final

from pytex.commands.cleveref import Crefname, CrefnameUpper
from pytex.interface.tex import TeX
from pytex.model.concat import Concat
from pytex.registry import Registry

_GERMAN_NAMES: Final[dict[str, tuple[str, str]]] = {
    "figure": ("Abbildung", "Abbildungen"),
    "table": ("Tabelle", "Tabellen"),
    "equation": ("Gleichung", "Gleichungen"),
    "chapter": ("Kapitel", "Kapitel"),
    "section": ("Abschnitt", "Abschnitte"),
    "subsection": ("Unterabschnitt", "Unterabschnitte"),
    "subsubsection": ("Unterunterabschnitt", "Unterunterabschnitte"),
    "listing": ("Listing", "Codeblock"),
    "appendix": ("Anhang", "Anhänge"),
    "algorithm": ("Algorithmus", "Algorithmen"),
    "theorem": ("Theorem", "Theoreme"),
    "lemma": ("Lemma", "Lemmata"),
    "corollary": ("Korollar", "Korollare"),
    "proposition": ("Proposition", "Propositionen"),
    "definition": ("Definition", "Definitionen"),
    "example": ("Beispiel", "Beispiele"),
    "remark": ("Bemerkung", "Bemerkungen"),
    "footnote": ("Fußnote", "Fußnoten"),
    "enumi": ("Punkt", "Punkte"),
    "enumii": ("Punkt", "Punkte"),
    "enumiii": ("Punkt", "Punkte"),
    "enumiv": ("Punkt", "Punkte"),
    "page": ("Seite", "Seiten"),
    "line": ("Zeile", "Zeilen"),
}


@Registry.add
def GermanCrefNames() -> TeX:
    """All Cref/crefname pairs for German typesetting. Emit once in preamble."""
    parts: list[TeX] = []
    for typ, (sg, pl) in _GERMAN_NAMES.items():
        parts.append(Crefname(typ, sg, pl))
        parts.append(CrefnameUpper(typ, sg, pl))
    return Concat(*parts)
