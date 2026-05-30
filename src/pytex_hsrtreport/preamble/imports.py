"""Required LaTeX packages + fallback font commands."""

from pytex import BuiltinPackages, Package, ProvideCommand, TeX
from pytex_komascript.model import Block

#: Packages that the original ``Imports.tex`` pulled in.
IMPORTS_PACKAGES: set[Package | str] = {
    Package(name="babel", options="ngerman"),
    Package(name="fontenc", options="T1"),
    Package(name="geometry", options="a4paper,top=2cm,bottom=2cm,left=2cm,right=2cm"),
    BuiltinPackages.CALC.value,
    BuiltinPackages.XFP.value,
    BuiltinPackages.KEYVAL.value,
    BuiltinPackages.IFTHEN.value,
    BuiltinPackages.ETOOLBOX.value,
    BuiltinPackages.EXPL3.value,
    BuiltinPackages.L3KEYS2E.value,
    BuiltinPackages.PDFTEXCMDS.value,
    BuiltinPackages.GRAPHICX.value,
    BuiltinPackages.XCOLOR.value,
    BuiltinPackages.ENVIRON.value,
    BuiltinPackages.BOPHOOK.value,
    BuiltinPackages.ARRAYJOBX.value,
    BuiltinPackages.LIPSUM.value,
    BuiltinPackages.TABULARX.value,
    BuiltinPackages.LONGTABLE.value,
    BuiltinPackages.MULTIROW.value,
    BuiltinPackages.ARYDSHLN.value,
    BuiltinPackages.ARRAY.value,
    BuiltinPackages.ENUMITEM.value,
    BuiltinPackages.CAPTION.value,
    Package(name="subcaption", options="subrefformat=parens"),
    BuiltinPackages.FLOATROW.value,
    BuiltinPackages.PIFONT.value,
    BuiltinPackages.FONTAWESOME5.value,
    BuiltinPackages.TIKZ.value,
    BuiltinPackages.PGF.value,
    BuiltinPackages.PGFFOR.value,
    BuiltinPackages.CHNGCNTR.value,
    BuiltinPackages.SETSPACE.value,
    BuiltinPackages.ACCSUPP.value,
    Package(name="mdframed", options="framemethod=TikZ"),
    BuiltinPackages.MULTICOL.value,
    BuiltinPackages.HYPERREF.value,
    BuiltinPackages.LISTINGS.value,
    BuiltinPackages.NEEDSPACE.value,
    BuiltinPackages.AFTERPAGE.value,
    BuiltinPackages.PLACEINS.value,
    Package(name="scrlayer-scrpage", options="singlespacing=true"),
    Package(name="glossaries", options="acronym, savenumberlist=true"),
    BuiltinPackages.RAGGED2E.value,
    BuiltinPackages.LMODERN.value,
    BuiltinPackages.CLEVEREF.value,
    BuiltinPackages.CSQUOTES.value,
    BuiltinPackages.DRAFTWATERMARK.value,
    BuiltinPackages.FP.value,
    BuiltinPackages.TIKZPAGENODES.value,
    BuiltinPackages.HYPHENAT.value,
}


def imports_block() -> TeX:
    """Fallback font commands. Packages live in :data:`IMPORTS_PACKAGES`."""
    return Block(
        ProvideCommand("blenderfont", "\\sffamily"),
        ProvideCommand("dinfont", "\\rmfamily"),
    )


__all__ = ["IMPORTS_PACKAGES", "imports_block"]
