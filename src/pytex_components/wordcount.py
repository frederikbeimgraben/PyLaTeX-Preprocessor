from pytex.commands.definitions import Newcommand
from pytex.interface.tex import TeX
from pytex.model.concat import Concat
from pytex.model.raw import Raw
from pytex.registry import Registry

__all__ = ["WordcountCommands"]


@Registry.add
def WordcountCommands() -> TeX:
    """Define `\\quickwordcount{<doc>}` + `\\detailtexcount{<doc>}` macros.

    Both shell out to `texcount` and require `-shell-escape` build.
    """
    return Concat(
        Newcommand(
            r"\quickwordcount",
            Raw(
                r"\immediate\write18{texcount -1 -sum -merge -q #1.tex > Build/words.sum }"  # noqa: E501
                + r"\input{Build/words.sum} words"
            ),
            nargs=1,
        ),
        Newcommand(
            r"\detailtexcount",
            Raw(
                r"\immediate\write18{texcount -merge -sum -q #1.tex > Build/.wcdetail }"
                + r"\verbatiminput{Build/.wcdetail}"
            ),
            nargs=1,
        ),
    )
