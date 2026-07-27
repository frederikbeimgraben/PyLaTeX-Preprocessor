from pytex.commands.biblatex import Citeauthor, Citeyear
from pytex.commands.hyperref import Hyperlink
from pytex.interface.tex import TeX
from pytex.model.concat import Concat
from pytex.registry import Registry

__all__ = ["Fcite"]


@Registry.add
def Fcite(key: str) -> TeX:
    """Return a clickable citation `\\hyperlink{cite.0@KEY}{Author, Year}`.

    The factory matches the `\\fcite` macro from HSRTReport. It puts the
    author and the year into one clickable link.

    biblatex names the citation anchor `cite.0@KEY`. The `0@` part is
    refsection 0. A link to `cite.KEY` finds no anchor and dangles.
    """
    return Hyperlink(
        f"cite.0@{key}",
        Concat(Citeauthor(key), ", ", Citeyear(key)),
    )
