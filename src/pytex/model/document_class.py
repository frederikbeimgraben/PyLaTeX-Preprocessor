from pytex.model.empty import Empty

from ..interface.package import PackageOption
from ..registry import Registry
from .control_sequence import ControlSequence, Parameter
from .raw import Raw


def _render_options(options: set[PackageOption] | frozenset[PackageOption]) -> str:
    return ",".join(
        item if isinstance(item, str) else f"{item[0]}={item[1]}" for item in options
    )


@Registry.add
def DocumentClass(
    name: str,
    options: set[PackageOption] | frozenset[PackageOption] | None = None,
):
    options = options or set()
    rendered = _render_options(options)
    opt_param = (
        Parameter(Raw(rendered), optional=True) if rendered else Empty
    )
    return ControlSequence(
        "documentclass",
        (opt_param, Parameter(name)),
    )
