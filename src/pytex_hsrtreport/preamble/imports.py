"""Packages with non-default options and the fallback font commands.

Packages without options are auto-collected from the TeX tree via
``Document.required_packages``. The set below is intentionally small —
either the package needs explicit options, or no node in the tree implies
it but it is still mandatory (in which case it lives behind a
:class:`pytex.RequirePackages` anchor).
"""

from pytex import (
    BuiltinPackages,
    Package,
    ProvideCommand,
    RequirePackages,
    TeX,
)
from pytex_komascript.model import Block

#: Packages that require explicit options or are mandatory but not implied
#: by any other tree node. Auto-collection picks up everything else.
PACKAGES_WITH_OPTIONS: set[Package] = {
    Package(name="babel", options="ngerman"),
    Package(name="fontenc", options="T1"),
    Package(name="geometry", options="a4paper,top=2cm,bottom=2cm,left=2cm,right=2cm"),
    Package(name="subcaption", options="subrefformat=parens"),
    Package(name="mdframed", options="framemethod=TikZ"),
    Package(name="scrlayer-scrpage", options="singlespacing=true"),
    Package(name="glossaries", options="acronym, savenumberlist=true"),
}

#: Bare packages with no options that nothing else pulls in.
_MUST_LOAD: tuple[Package, ...] = (
    BuiltinPackages.AMSMATH.value,  # Must be before cleveref
    BuiltinPackages.LMODERN.value,
    BuiltinPackages.CALC.value,
    BuiltinPackages.SETSPACE.value,
    BuiltinPackages.NEEDSPACE.value,
    BuiltinPackages.PLACEINS.value,
    BuiltinPackages.CAPTION.value,
    BuiltinPackages.ENUMITEM.value,
    BuiltinPackages.TIKZPAGENODES.value,
    BuiltinPackages.PGFFOR.value,
    BuiltinPackages.GRAPHICX.value,
)


def ImportsBlock() -> TeX:
    """Anchor mandatory packages + fallback font commands."""
    return Block(
        RequirePackages(*_MUST_LOAD),
        ProvideCommand("blenderfont", "\\sffamily"),
        ProvideCommand("dinfont", "\\rmfamily"),
    )


__all__ = ["PACKAGES_WITH_OPTIONS", "ImportsBlock"]
