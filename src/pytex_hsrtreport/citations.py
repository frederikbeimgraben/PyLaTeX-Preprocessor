from pytex.commands.biblatex import Citeauthor, Citeyear
from pytex.commands.hyperref import Hyperlink
from pytex.interface.tex import TeX
from pytex.model.concat import Concat
from pytex.registry import Registry

__all__ = ["Fcite"]


@Registry.add
def Fcite(key: str) -> TeX:
    """Full clickable citation: `\\hyperlink{cite.0@KEY}{Author, Year}`.

    Mirrors HSRTReport's `\\fcite` macro — author + year in one clickable link.
    biblatex names the citation anchor ``cite.0@KEY`` (the ``0@`` is refsection
    0); targeting ``cite.KEY`` would dangle.
    """
    return Hyperlink(
        f"cite.0@{key}",
        Concat(Citeauthor(key), ", ", Citeyear(key)),
    )
