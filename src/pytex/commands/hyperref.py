"""Factories for the `hyperref` package."""

from ..helpers.with_package import with_package
from ..interface.tex import TeX
from ..model.control_sequence import ControlSequence, Parameter
from ..packages import HYPERREF
from ..registry import Registry

__all__ = [
    "Autoref",
    "Href",
    "Hyperlink",
    "Hypersetup",
    "Hypertarget",
    "Nolinkurl",
    "Url",
]


@Registry.add
@with_package(HYPERREF)
def Hypersetup(options: dict[str, str]) -> TeX:
    """Render `\\hypersetup`, which sets the hyperref options.

    Args:
        options: hyperref options, for example `{"colorlinks": "true"}`. The
            factory renders them as `key=value` pairs and joins the pairs with
            commas.
    """
    return ControlSequence("hypersetup", (Parameter(options),))


@Registry.add
@with_package(HYPERREF)
def Href(url: str, text: TeX | str) -> TeX:
    """Render `\\href`, which prints the text as a link to a URL."""
    return ControlSequence("href", (Parameter(url), Parameter(text)))


@Registry.add
@with_package(HYPERREF)
def Url(url: str) -> TeX:
    """Render `\\url`, which prints a URL and makes it a link."""
    return ControlSequence("url", (Parameter(url),))


@Registry.add
@with_package(HYPERREF)
def Nolinkurl(url: str) -> TeX:
    """Render `\\nolinkurl`, which prints a URL but makes no link."""
    return ControlSequence("nolinkurl", (Parameter(url),))


@Registry.add
@with_package(HYPERREF)
def Hyperlink(name: str, text: TeX | str) -> TeX:
    """Render `\\hyperlink`, a link to a target inside the document.

    Args:
        name: The target name that `Hypertarget` set.
    """
    return ControlSequence("hyperlink", (Parameter(name), Parameter(text)))


@Registry.add
@with_package(HYPERREF)
def Hypertarget(name: str, text: TeX | str) -> TeX:
    """Render `\\hypertarget`, which marks a target for `Hyperlink`."""
    return ControlSequence("hypertarget", (Parameter(name), Parameter(text)))


@Registry.add
@with_package(HYPERREF)
def Autoref(name: str) -> TeX:
    """Render `\\autoref`, a reference that prints the type name and the number.

    Args:
        name: The label name, as `\\label` set it.
    """
    return ControlSequence("autoref", (Parameter(name),))
