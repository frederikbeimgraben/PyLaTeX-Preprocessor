"""Factories for the `cleveref` package."""

from ..helpers.with_package import with_package
from ..interface.tex import TeX
from ..model.control_sequence import ControlSequence, Parameter
from ..packages import CLEVEREF
from ..registry import Registry

__all__ = ["Cref", "CrefUpper", "Crefformat", "Crefname", "CrefnameUpper"]


@Registry.add
@with_package(CLEVEREF)
def Cref(*labels: str) -> TeX:
    """Render `\\cref`, a reference that also prints the type name.

    The factory joins the labels with commas, so cleveref prints one list.
    """
    return ControlSequence("cref", (Parameter(",".join(labels)),))


@Registry.add
@with_package(CLEVEREF)
def CrefUpper(*labels: str) -> TeX:
    """Render `\\Cref`, the capitalized form of `\\cref`.

    The factory joins the labels with commas, so cleveref prints one list.
    """
    return ControlSequence("Cref", (Parameter(",".join(labels)),))


@Registry.add
@with_package(CLEVEREF)
def Crefname(typ: str, singular: str, plural: str) -> TeX:
    """Render `\\crefname`, which names a reference type.

    Args:
        typ: The reference type, for example `figure` or `equation`.
    """
    return ControlSequence(
        "crefname",
        (Parameter(typ), Parameter(singular), Parameter(plural)),
    )


@Registry.add
@with_package(CLEVEREF)
def CrefnameUpper(typ: str, singular: str, plural: str) -> TeX:
    """Render `\\Crefname`, which names a reference type for `\\Cref`."""
    return ControlSequence(
        "Crefname",
        (Parameter(typ), Parameter(singular), Parameter(plural)),
    )


@Registry.add
@with_package(CLEVEREF)
def Crefformat(typ: str, fmt: str) -> TeX:
    """Render `\\crefformat`, which sets the format of one reference type.

    Args:
        fmt: The format text. cleveref replaces `#1` with the reference
            number. It replaces `#2` and `#3` with the start and the end of
            the hyperlink.
    """
    return ControlSequence("crefformat", (Parameter(typ), Parameter(fmt)))
