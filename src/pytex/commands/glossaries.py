from ..helpers.with_package import with_package
from ..interface.tex import TeX
from ..model.control_sequence import ControlSequence, Parameter
from ..packages import GLOSSARIES
from ..registry import Registry


@Registry.add
@with_package(GLOSSARIES)
def Makeglossaries() -> TeX:
    return ControlSequence("makeglossaries", ())


@Registry.add
@with_package(GLOSSARIES)
def Newglossaryentry(label: str, fields: dict[str, str]) -> TeX:
    return ControlSequence(
        "newglossaryentry",
        (Parameter(label), Parameter(fields)),
    )


@Registry.add
@with_package(GLOSSARIES)
def Newacronym(label: str, short: str, long: str) -> TeX:
    return ControlSequence(
        "newacronym",
        (Parameter(label), Parameter(short), Parameter(long)),
    )


@Registry.add
@with_package(GLOSSARIES)
def Printglossary(options: dict[str, str] | None = None) -> TeX:
    if options is None:
        return ControlSequence("printglossary", ())
    return ControlSequence(
        "printglossary",
        (Parameter(options, optional=True),),
    )


@Registry.add
@with_package(GLOSSARIES)
def Printacronyms(options: dict[str, str] | None = None) -> TeX:
    if options is None:
        return ControlSequence("printacronyms", ())
    return ControlSequence(
        "printacronyms",
        (Parameter(options, optional=True),),
    )


@Registry.add
@with_package(GLOSSARIES)
def Gls(label: str) -> TeX:
    return ControlSequence("gls", (Parameter(label),))


@Registry.add
@with_package(GLOSSARIES)
def Glsupper(label: str) -> TeX:
    return ControlSequence("Gls", (Parameter(label),))


@Registry.add
@with_package(GLOSSARIES)
def Glspl(label: str) -> TeX:
    return ControlSequence("glspl", (Parameter(label),))


@Registry.add
@with_package(GLOSSARIES)
def Glsplupper(label: str) -> TeX:
    return ControlSequence("Glspl", (Parameter(label),))


@Registry.add
@with_package(GLOSSARIES)
def Acrshort(label: str) -> TeX:
    return ControlSequence("acrshort", (Parameter(label),))


@Registry.add
@with_package(GLOSSARIES)
def Acrlong(label: str) -> TeX:
    return ControlSequence("acrlong", (Parameter(label),))


@Registry.add
@with_package(GLOSSARIES)
def Acrfull(label: str) -> TeX:
    return ControlSequence("acrfull", (Parameter(label),))


@Registry.add
@with_package(GLOSSARIES)
def Setglossarystyle(name: str) -> TeX:
    return ControlSequence("setglossarystyle", (Parameter(name),))


@Registry.add
@with_package(GLOSSARIES)
def Glsenablehyper() -> TeX:
    return ControlSequence("glsenablehyper", ())
