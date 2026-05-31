from ..interface.tex import TeX
from ..model.raw import Raw


def coerce_tex(value: TeX | str) -> TeX:
    if isinstance(value, TeX):
        return value

    return Raw(value)
