from pytex.interface.tex import TeX
from pytex.model.raw import Raw


def coerce_tex(value: TeX | str) -> TeX:
    if isinstance(value, TeX):
        return value

    return Raw(value)
