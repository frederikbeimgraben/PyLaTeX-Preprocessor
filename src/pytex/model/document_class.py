from .control_sequence import ControlSequence, Parameter


def DocumentClass(name: str, params: dict[str, str]):
    return ControlSequence(
        "documentclass",
        (
            Parameter(params, optional=True),
            Parameter(name),
        ),
    )
