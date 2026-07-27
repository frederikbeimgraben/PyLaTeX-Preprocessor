from pytex.interface.tex import TeX
from pytex.model.control_sequence import ControlSequence, Parameter
from pytex.model.environment import Environment
from pytex.model.raw import Raw
from pytex.registry import Registry

__all__ = [
    "Conditionalpagebreak",
    "Critical",
    "Keeptogether",
    "Smartsection",
    "Smartsubsection",
]


@Registry.add
def Keeptogether(body: TeX | str) -> TeX:
    """Wrap `body` in a minipage, so that it stays on one page.

    LaTeX never breaks a minipage across a page boundary. A body that is
    taller than the text block overflows the page instead.
    """
    return Environment("minipage", body, (Parameter(r"\linewidth"),))


@Registry.add
def Conditionalpagebreak(amount: str = "10\\baselineskip") -> TeX:
    """Ask for `amount` of free space, and break the page when less is left.

    Args:
        amount: A LaTeX length. The default is `10\\baselineskip`.

    Note:
        The factory does not require the `needspace` package. The document
        must load that package itself.
    """
    return ControlSequence("needspace", (Parameter(amount),))


@Registry.add
def Critical(body: TeX | str) -> TeX:
    """Wrap `body` in a `samepage` environment with the highest penalties.

    The penalties stop LaTeX from breaking the page between two lines of
    `body`, and they stop widow and orphan lines.

    The factory renders `body` at once and puts the result in a `Raw` node.
    A package that `body` requires never reaches the preamble. Require such a
    package in the document yourself.
    """
    return Environment(
        "samepage",
        Raw(
            r"\interlinepenalty=10000\widowpenalty=10000\clubpenalty=10000"
            + str(body if isinstance(body, str) else body.rendered)
        ),
    )


@Registry.add
def Smartsection(title: TeX | str, short: TeX | str | None = None) -> TeX:
    """Start a section that first asks for `\\sectionminspace` of free space.

    When less space is left, LaTeX breaks the page before the heading. The
    document must define the length `\\sectionminspace` and load the
    `needspace` package. `pytex_hsrtreport` does both.

    The factory renders the heading at once and puts the result in a `Raw`
    node. A package that `title` requires never reaches the preamble. Require
    such a package in the document yourself.
    """
    head = (
        ControlSequence("section", (Parameter(title),))
        if short is None
        else ControlSequence(
            "section",
            (Parameter(short, optional=True), Parameter(title)),
        )
    )
    return Raw(
        r"\vfil\penalty-9999\vfilneg\needspace{\sectionminspace}" + head.rendered
    )


@Registry.add
def Smartsubsection(title: TeX | str, short: TeX | str | None = None) -> TeX:
    """Start a subsection that first asks for `\\subsectionminspace` of space.

    When less space is left, LaTeX breaks the page before the heading. The
    document must define the length `\\subsectionminspace` and load the
    `needspace` package. `pytex_hsrtreport` does both.

    The factory renders the heading at once and puts the result in a `Raw`
    node. A package that `title` requires never reaches the preamble. Require
    such a package in the document yourself.
    """
    head = (
        ControlSequence("subsection", (Parameter(title),))
        if short is None
        else ControlSequence(
            "subsection",
            (Parameter(short, optional=True), Parameter(title)),
        )
    )
    return Raw(
        r"\vfil\penalty-9999\vfilneg\needspace{\subsectionminspace}" + head.rendered
    )
