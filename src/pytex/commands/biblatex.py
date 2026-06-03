from ..helpers.with_package import with_package
from ..interface.tex import TeX
from ..model.control_sequence import ControlSequence, Parameter
from ..packages import BIBLATEX
from ..registry import Registry

__all__ = [
    "Addbibresource",
    "Autocite",
    "Citeauthor",
    "Citetitle",
    "Citeyear",
    "ExecuteBibliographyOptions",
    "Footcite",
    "Nocite",
    "Parencite",
    "Printbibliography",
    "Textcite",
]


@Registry.add
@with_package(BIBLATEX)
def Addbibresource(path: str) -> TeX:
    return ControlSequence("addbibresource", (Parameter(path),))


@Registry.add
@with_package(BIBLATEX)
def Printbibliography(
    heading: str | None = None,
    title: str | None = None,
) -> TeX:
    opts = [
        f"{key}={value}"
        for key, value in (("heading", heading), ("title", title))
        if value is not None
    ]
    if not opts:
        return ControlSequence("printbibliography", ())
    return ControlSequence(
        "printbibliography",
        (Parameter(",".join(opts), optional=True),),
    )


@Registry.add
@with_package(BIBLATEX)
def Textcite(*keys: str) -> TeX:
    return ControlSequence("textcite", (Parameter(",".join(keys)),))


@Registry.add
@with_package(BIBLATEX)
def Parencite(*keys: str) -> TeX:
    return ControlSequence("parencite", (Parameter(",".join(keys)),))


@Registry.add
@with_package(BIBLATEX)
def Autocite(*keys: str, postnote: str | None = None) -> TeX:
    key_param = Parameter(",".join(keys))
    if postnote is None:
        return ControlSequence("autocite", (key_param,))
    # A single optional argument to \autocite is the postnote (e.g. a page).
    return ControlSequence("autocite", (Parameter(postnote, optional=True), key_param))


@Registry.add
@with_package(BIBLATEX)
def Footcite(*keys: str) -> TeX:
    return ControlSequence("footcite", (Parameter(",".join(keys)),))


@Registry.add
@with_package(BIBLATEX)
def Citeauthor(key: str) -> TeX:
    return ControlSequence("citeauthor", (Parameter(key),))


@Registry.add
@with_package(BIBLATEX)
def Citeyear(key: str) -> TeX:
    return ControlSequence("citeyear", (Parameter(key),))


@Registry.add
@with_package(BIBLATEX)
def Citetitle(key: str) -> TeX:
    return ControlSequence("citetitle", (Parameter(key),))


@Registry.add
@with_package(BIBLATEX)
def Nocite(*keys: str) -> TeX:
    return ControlSequence("nocite", (Parameter(",".join(keys)),))


@Registry.add
@with_package(BIBLATEX)
def ExecuteBibliographyOptions(options: dict[str, str]) -> TeX:
    return ControlSequence("ExecuteBibliographyOptions", (Parameter(options),))
