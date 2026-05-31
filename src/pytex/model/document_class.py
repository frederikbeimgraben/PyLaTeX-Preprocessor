from pytex.model.empty import Empty

from .control_sequence import ControlSequence, Parameter


def DocumentClass(name: str, params: dict[str, str]):
    return ControlSequence(
        "documentclass",
        (
            Parameter(params, optional=True) if len(params) != 0 else Empty,
            Parameter(name),
        ),
    )
