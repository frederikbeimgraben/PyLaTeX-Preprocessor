"""Catalogue of commonly-used LaTeX packages as :class:`Package` constants.

The :class:`BuiltinPackages` enum gives every package a stable Python handle so
downstream documents can build their package list with autocomplete instead of
free strings; per-document options are added with
``BuiltinPackages.<NAME>.value.with_options(...)`` when needed.
"""

from enum import Enum

from ...model.base_model import Package


class BuiltinPackages(Enum):
    """Well-known LaTeX packages keyed by an upper-case Python identifier.

    Values are :class:`Package` instances without options; use
    :meth:`Package.with_options` to derive a Package with options where the
    caller cares.
    """

    # --- Localisation / fonts ---
    BABEL = Package(name="babel")
    FONTENC = Package(name="fontenc")
    INPUTENC = Package(name="inputenc")
    LMODERN = Package(name="lmodern")
    FONTSPEC = Package(name="fontspec")
    FONTAWESOME5 = Package(name="fontawesome5")
    PIFONT = Package(name="pifont")
    HYPHENAT = Package(name="hyphenat")
    RAGGED2E = Package(name="ragged2e")
    CSQUOTES = Package(name="csquotes")

    # --- Geometry / layout ---
    GEOMETRY = Package(name="geometry")
    SETSPACE = Package(name="setspace")
    SCRLAYER_SCRPAGE = Package(name="scrlayer-scrpage")
    NEEDSPACE = Package(name="needspace")
    AFTERPAGE = Package(name="afterpage")
    PLACEINS = Package(name="placeins")
    MULTICOL = Package(name="multicol")

    # --- Helpers / control structures ---
    CALC = Package(name="calc")
    XFP = Package(name="xfp")
    FP = Package(name="fp")
    KEYVAL = Package(name="keyval")
    IFTHEN = Package(name="ifthen")
    ETOOLBOX = Package(name="etoolbox")
    EXPL3 = Package(name="expl3")
    L3KEYS2E = Package(name="l3keys2e")
    PDFTEXCMDS = Package(name="pdftexcmds")
    ENVIRON = Package(name="environ")
    BOPHOOK = Package(name="bophook")
    ARRAYJOBX = Package(name="arrayjobx")
    LIPSUM = Package(name="lipsum")

    # --- Tables / arrays ---
    TABULARX = Package(name="tabularx")
    LONGTABLE = Package(name="longtable")
    MULTIROW = Package(name="multirow")
    ARYDSHLN = Package(name="arydshln")
    ARRAY = Package(name="array")
    ENUMITEM = Package(name="enumitem")

    # --- Figures / captions ---
    GRAPHICX = Package(name="graphicx")
    CAPTION = Package(name="caption")
    SUBCAPTION = Package(name="subcaption")
    FLOATROW = Package(name="floatrow")

    # --- Color / boxes ---
    XCOLOR = Package(name="xcolor")
    MDFRAMED = Package(name="mdframed")

    # --- Graphics / TikZ ---
    TIKZ = Package(name="tikz")
    PGF = Package(name="pgf")
    PGFFOR = Package(name="pgffor")
    TIKZPAGENODES = Package(name="tikzpagenodes")

    # --- Counters ---
    CHNGCNTR = Package(name="chngcntr")

    # --- Accessibility ---
    ACCSUPP = Package(name="accsupp")

    # --- Hyperlinks / cross-references ---
    HYPERREF = Package(name="hyperref")
    # cleveref insists on being loaded after hyperref and amsmath (whenever
    # amsmath is in scope, which happens transitively through many packages).
    CLEVEREF = Package(
        name="cleveref",
        requires=frozenset({"hyperref", "amsmath"}),
    )

    # --- Source code listings ---
    LISTINGS = Package(name="listings")

    # --- Glossaries / acronyms ---
    GLOSSARIES = Package(name="glossaries")

    # --- Bibliography ---
    BIBLATEX = Package(name="biblatex")
    NATBIB = Package(name="natbib")

    # --- Drafts / watermark ---
    DRAFTWATERMARK = Package(name="draftwatermark")

    # --- Math ---
    AMSMATH = Package(name="amsmath")
    AMSSYMB = Package(name="amssymb")


__all__ = ["BuiltinPackages"]
