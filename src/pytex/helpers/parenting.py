"""Set the parent node on the child nodes of a TeX node."""

from contextlib import suppress

from ..interface.tex import TeX
from ..model.empty import Empty

__all__ = ["attach"]


def attach(parent: TeX, *children: object) -> None:
    """Set the parent node of each TeX child to `parent`.

    The function writes `_parent` with `object.__setattr__`, because a frozen
    dataclass rejects a normal attribute assignment. The function skips a
    child that is not a TeX node. It also skips, without an error, a child
    that refuses the attribute. A node with `slots` and no `_parent` slot is
    such a child. It also skips the shared `Empty` singleton, which every
    document without a preamble or parameter reuses.
    """
    for child in children:
        if isinstance(child, TeX) and child is not Empty:
            with suppress(AttributeError, TypeError):
                object.__setattr__(child, "_parent", parent)
