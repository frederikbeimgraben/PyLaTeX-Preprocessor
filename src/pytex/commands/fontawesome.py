from ..helpers.with_package import with_package
from ..interface.tex import TeX
from ..model.control_sequence import ControlSequence, Parameter
from ..packages import FONTAWESOME5
from ..registry import Registry


@Registry.add
@with_package(FONTAWESOME5)
def FaIcon(name: str) -> TeX:
    return ControlSequence("faIcon", (Parameter(name),))


def _icon(name: str) -> TeX:
    return ControlSequence(name, ())


@Registry.add
@with_package(FONTAWESOME5)
def FaInfoCircle() -> TeX:
    return _icon("faInfoCircle")


@Registry.add
@with_package(FONTAWESOME5)
def FaExclamationTriangle() -> TeX:
    return _icon("faExclamationTriangle")


@Registry.add
@with_package(FONTAWESOME5)
def FaExclamationCircle() -> TeX:
    return _icon("faExclamationCircle")


@Registry.add
@with_package(FONTAWESOME5)
def FaCheckCircle() -> TeX:
    return _icon("faCheckCircle")


@Registry.add
@with_package(FONTAWESOME5)
def FaVoteYea() -> TeX:
    return _icon("faVoteYea")


@Registry.add
@with_package(FONTAWESOME5)
def FaQuestionCircle() -> TeX:
    return _icon("faQuestionCircle")


@Registry.add
@with_package(FONTAWESOME5)
def FaBookmark() -> TeX:
    return _icon("faBookmark")


@Registry.add
@with_package(FONTAWESOME5)
def FaCog() -> TeX:
    return _icon("faCog")


@Registry.add
@with_package(FONTAWESOME5)
def FaGithub() -> TeX:
    return _icon("faGithub")
