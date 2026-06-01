from pytex.model.empty import Empty

from ..helpers.with_package import with_package
from ..interface.tex import TeX
from ..model.control_sequence import ControlSequence, Parameter
from ..packages import FONTAWESOME
from ..registry import Registry


@Registry.add
@with_package(FONTAWESOME)
def FaIcon(name: str | None) -> TeX:
    # fontawesome (v4) spells the generic helper lowercase; v5's \faIcon does
    # not exist here. The v4 package loads via Type1 fonts, so it survives
    # tectonic's XeTeX engine (fontawesome5's OTF load crashes it).
    return ControlSequence("faicon", (Parameter(name),)) if name is not None else Empty


def _icon(name: str) -> TeX:
    return ControlSequence(name, ())


@Registry.add
@with_package(FONTAWESOME)
def FaInfoCircle() -> TeX:
    return _icon("faInfoCircle")


@Registry.add
@with_package(FONTAWESOME)
def FaExclamationTriangle() -> TeX:
    return _icon("faExclamationTriangle")


@Registry.add
@with_package(FONTAWESOME)
def FaExclamationCircle() -> TeX:
    return _icon("faExclamationCircle")


@Registry.add
@with_package(FONTAWESOME)
def FaCheckCircle() -> TeX:
    return _icon("faCheckCircle")


@Registry.add
@with_package(FONTAWESOME)
def FaVoteYea() -> TeX:
    # No \faVoteYea macro in fontawesome v4; use the generic name lookup.
    return ControlSequence("faicon", (Parameter("vote-yea"),))


@Registry.add
@with_package(FONTAWESOME)
def FaQuestionCircle() -> TeX:
    return _icon("faQuestionCircle")


@Registry.add
@with_package(FONTAWESOME)
def FaBookmark() -> TeX:
    return _icon("faBookmark")


@Registry.add
@with_package(FONTAWESOME)
def FaCog() -> TeX:
    return _icon("faCog")


@Registry.add
@with_package(FONTAWESOME)
def FaGithub() -> TeX:
    return _icon("faGithub")
