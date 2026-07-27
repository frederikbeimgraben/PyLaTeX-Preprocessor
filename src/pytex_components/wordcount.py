from pytex.commands.definitions import Newcommand
from pytex.interface.tex import TeX
from pytex.model.concat import Concat
from pytex.model.raw import Raw
from pytex.registry import Registry

__all__ = ["WordcountCommands"]


@Registry.add
def WordcountCommands() -> TeX:
    """Define the macros `\\quickwordcount{<doc>}` and `\\detailtexcount{<doc>}`.

    Both macros run `texcount` through `\\write18`, so the compile pass needs
    shell-escape. A build with `--no-shell-escape` fails.

    Both macros write into the directory `Build`. `\\detailtexcount` reads the
    result back with `\\verbatiminput`. That macro needs the `verbatim`
    package.

    The directory name is fixed. The macros do not follow `--build-dir`, whose
    default is `build`. Create a directory named `Build` next to the rendered
    `.tex` file before the compile pass.
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
