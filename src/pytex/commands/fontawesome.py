"""Icon factories for the `fontawesome` package.

PyTeX uses fontawesome version 4, because that version loads Type1 fonts. The
`fontawesome5` package loads OTF fonts, and that load crashes the XeTeX engine
inside the tectonic binary.
"""

from pytex.model.empty import Empty

from ..helpers.with_package import with_package
from ..interface.tex import TeX
from ..model.control_sequence import ControlSequence, Parameter
from ..packages import FONTAWESOME
from ..registry import Registry

__all__ = [
    "FaBookmark",
    "FaCheckCircle",
    "FaCog",
    "FaExclamationCircle",
    "FaExclamationTriangle",
    "FaGithub",
    "FaIcon",
    "FaInfoCircle",
    "FaQuestionCircle",
    "FaVoteYea",
]


@Registry.add
@with_package(FONTAWESOME)
def FaIcon(name: str | None) -> TeX:
    """Render `\\faicon` for a named icon.

    Args:
        name: The fontawesome version 4 icon name, for example `check-circle`.
            If `name` is None, the factory returns an empty node.
    """
    # fontawesome version 4 spells the generic macro lowercase. The macro
    # `\faIcon` from version 5 does not exist here.
    return ControlSequence("faicon", (Parameter(name),)) if name is not None else Empty


def _icon(name: str) -> TeX:
    """Render an icon macro that takes no argument."""
    return ControlSequence(name, ())


@Registry.add
@with_package(FONTAWESOME)
def FaInfoCircle() -> TeX:
    """Render `\\faInfoCircle`, the information icon."""
    return _icon("faInfoCircle")


@Registry.add
@with_package(FONTAWESOME)
def FaExclamationTriangle() -> TeX:
    """Render `\\faExclamationTriangle`, the warning icon."""
    return _icon("faExclamationTriangle")


@Registry.add
@with_package(FONTAWESOME)
def FaExclamationCircle() -> TeX:
    """Render `\\faExclamationCircle`, the alert icon."""
    return _icon("faExclamationCircle")


@Registry.add
@with_package(FONTAWESOME)
def FaCheckCircle() -> TeX:
    """Render `\\faCheckCircle`, the check mark icon."""
    return _icon("faCheckCircle")


@Registry.add
@with_package(FONTAWESOME)
def FaVoteYea() -> TeX:
    """Render the `vote-yea` icon through the generic name lookup."""
    # fontawesome version 4 has no `\faVoteYea` macro. This factory asks for
    # the icon by name instead.
    return ControlSequence("faicon", (Parameter("vote-yea"),))


@Registry.add
@with_package(FONTAWESOME)
def FaQuestionCircle() -> TeX:
    """Render `\\faQuestionCircle`, the question icon."""
    return _icon("faQuestionCircle")


@Registry.add
@with_package(FONTAWESOME)
def FaBookmark() -> TeX:
    """Render `\\faBookmark`, the bookmark icon."""
    return _icon("faBookmark")


@Registry.add
@with_package(FONTAWESOME)
def FaCog() -> TeX:
    """Render `\\faCog`, the gear icon."""
    return _icon("faCog")


@Registry.add
@with_package(FONTAWESOME)
def FaGithub() -> TeX:
    """Render `\\faGithub`, the GitHub icon."""
    return _icon("faGithub")
