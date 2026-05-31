from pytex.interface.control_sequence import Parameters
from pytex.interface.tex import TeX
from pytex.model.concat import Concat
from pytex.model.control_sequence import ControlSequence, Parameter
from pytex.model.raw import Raw


def Begin(name: str, params: Parameters = None):
    _params = params or ()

    return ControlSequence(
        "begin",
        (Parameter(Raw(name)), *_params),
    )


def End(name: str):
    return ControlSequence("end", (Parameter(Raw(name)),))


def Environment(name: str, body: TeX | str, params: Parameters = None) -> TeX:
    return Concat(
        Begin(name, params),
        body,
        End(name),
    )
