from ..interface.control_sequence import Parameters
from ..interface.tex import TeX
from ..registry import Registry
from .concat import Concat
from .control_sequence import ControlSequence, Parameter
from .raw import Raw

__all__ = ["Begin", "End", "Environment"]


@Registry.add
def Begin(name: str, params: Parameters = None) -> TeX:
    return ControlSequence(
        "begin",
        (Parameter(Raw(name)), *(params or ())),
    )


@Registry.add
def End(name: str) -> TeX:
    return ControlSequence("end", (Parameter(Raw(name)),))


@Registry.add
def Environment(name: str, body: TeX | str, params: Parameters = None) -> TeX:
    return Concat(
        Begin(name, params),
        body,
        End(name),
    )
