from pytex.commands.biblatex import Citeauthor, Citeyear
from pytex.commands.hyperref import Hyperlink
from pytex.interface.tex import TeX
from pytex.model.concat import Concat
from pytex.registry import Registry


@Registry.add
def Fcite(key: str) -> TeX:
    """Full clickable citation: `\\hyperlink{cite.KEY}{Author, Year}`.

    Mirrors HSRTReport's `\\fcite` macro — author + year in one clickable link.
    """
    return Hyperlink(
        f"cite.{key}",
        Concat(Citeauthor(key), ", ", Citeyear(key)),
    )
