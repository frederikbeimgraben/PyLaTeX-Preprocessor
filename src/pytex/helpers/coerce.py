from ..interface.tex import TeX
from ..model.raw import Raw
from ..registry import Registry

__all__ = ["coerce_tex"]


@Registry.add
def coerce_tex(value: TeX | str) -> TeX:
    if isinstance(value, TeX):
        return value

    return Raw(value)
