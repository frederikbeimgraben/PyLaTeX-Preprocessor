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
    """Wraps body in a minipage to keep it on the same page."""
    return Environment("minipage", body, (Parameter(r"\linewidth"),))


@Registry.add
def Conditionalpagebreak(amount: str = "10\\baselineskip") -> TeX:
    return ControlSequence("needspace", (Parameter(amount),))


@Registry.add
def Critical(body: TeX | str) -> TeX:
    """High-penalty samepage env: prevents widows/clubs/linebreaks inside."""
    return Environment(
        "samepage",
        Raw(
            r"\interlinepenalty=10000\widowpenalty=10000\clubpenalty=10000"
            + str(body if isinstance(body, str) else body.rendered)
        ),
    )


@Registry.add
def Smartsection(title: TeX | str, short: TeX | str | None = None) -> TeX:
    """Section that asks for `\\sectionminspace` before breaking the page."""
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
