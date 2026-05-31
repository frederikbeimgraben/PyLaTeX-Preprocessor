from ..interface.control_sequence import Parameters
from ..interface.tex import TeX
from ..registry import Registry
from .concat import Concat
from .control_sequence import ControlSequence, Parameter
from .raw import Raw


@Registry.add
def Begin(name: str, params: Parameters = None):
    _params = params or ()

    return ControlSequence(
        "begin",
        (Parameter(Raw(name)), *_params),
    )


@Registry.add
def End(name: str):
    return ControlSequence("end", (Parameter(Raw(name)),))


@Registry.add
def Environment(name: str, body: TeX | str, params: Parameters = None) -> TeX:
    return Concat(
        Begin(name, params),
        body,
        End(name),
    )
