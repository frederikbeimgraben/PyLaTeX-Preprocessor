from pytex.helpers.with_package import with_package
from pytex.interface.tex import TeX
from pytex.model.control_sequence import ControlSequence, Parameter
from pytex.model.environment import Environment
from pytex.packages import SCRLAYER_SCRPAGE, TYPEAREA
from pytex.registry import Registry


def _sectioning(name: str, title: TeX | str, short: TeX | str | None) -> TeX:
    if short is None:
        return ControlSequence(name, (Parameter(title),))
    return ControlSequence(name, (Parameter(short, optional=True), Parameter(title)))


@Registry.add
def Addpart(title: TeX | str, short: TeX | str | None = None) -> TeX:
    return _sectioning("addpart", title, short)


@Registry.add
def Addchap(title: TeX | str, short: TeX | str | None = None) -> TeX:
    return _sectioning("addchap", title, short)


@Registry.add
def Addsec(title: TeX | str, short: TeX | str | None = None) -> TeX:
    return _sectioning("addsec", title, short)


@Registry.add
def Minisec(title: TeX | str) -> TeX:
    return ControlSequence("minisec", (Parameter(title),))


@Registry.add
def Frontmatter() -> TeX:
    return ControlSequence("frontmatter", ())


@Registry.add
def Mainmatter() -> TeX:
    return ControlSequence("mainmatter", ())


@Registry.add
def Backmatter() -> TeX:
    return ControlSequence("backmatter", ())


@Registry.add
def Appendix() -> TeX:
    return ControlSequence("appendix", ())


@Registry.add
def Subtitle(text: TeX | str) -> TeX:
    return ControlSequence("subtitle", (Parameter(text),))


@Registry.add
def Subject(text: TeX | str) -> TeX:
    return ControlSequence("subject", (Parameter(text),))


@Registry.add
def Publishers(text: TeX | str) -> TeX:
    return ControlSequence("publishers", (Parameter(text),))


@Registry.add
def Titlehead(text: TeX | str) -> TeX:
    return ControlSequence("titlehead", (Parameter(text),))


@Registry.add
def Dedication(text: TeX | str) -> TeX:
    return ControlSequence("dedication", (Parameter(text),))


@Registry.add
def Uppertitleback(text: TeX | str) -> TeX:
    return ControlSequence("uppertitleback", (Parameter(text),))


@Registry.add
def Lowertitleback(text: TeX | str) -> TeX:
    return ControlSequence("lowertitleback", (Parameter(text),))


@Registry.add
def Extratitle(text: TeX | str) -> TeX:
    return ControlSequence("extratitle", (Parameter(text),))


@Registry.add
def Dictum(text: TeX | str, author: TeX | str | None = None) -> TeX:
    if author is None:
        return ControlSequence("dictum", (Parameter(text),))
    return ControlSequence(
        "dictum",
        (Parameter(author, optional=True), Parameter(text)),
    )


@Registry.add
def KOMAoptions(options: dict[str, str]) -> TeX:
    return ControlSequence("KOMAoptions", (Parameter(options),))


@Registry.add
def KOMAoption(key: str, value: str) -> TeX:
    return ControlSequence("KOMAoption", (Parameter(key), Parameter(value)))


@Registry.add
def Setkomafont(element: str, definition: TeX | str) -> TeX:
    return ControlSequence(
        "setkomafont",
        (Parameter(element), Parameter(definition)),
    )


@Registry.add
def Addtokomafont(element: str, definition: TeX | str) -> TeX:
    return ControlSequence(
        "addtokomafont",
        (Parameter(element), Parameter(definition)),
    )


@Registry.add
def Usekomafont(element: str) -> TeX:
    return ControlSequence("usekomafont", (Parameter(element),))


@Registry.add
def Captionabove(text: TeX | str) -> TeX:
    return ControlSequence("captionabove", (Parameter(text),))


@Registry.add
def Captionbelow(text: TeX | str) -> TeX:
    return ControlSequence("captionbelow", (Parameter(text),))


@Registry.add
def Marginline(text: TeX | str) -> TeX:
    return ControlSequence("marginline", (Parameter(text),))


@Registry.add
def Addmargin(body: TeX | str, amount: str) -> TeX:
    return Environment("addmargin", body, (Parameter(amount),))


@Registry.add
def Labeling(body: TeX | str, sep: str = "") -> TeX:
    params: tuple[Parameter, ...]
    if sep:
        params = (Parameter(sep, optional=True),)
    else:
        params = ()
    return Environment("labeling", body, params)


@Registry.add
@with_package(TYPEAREA)
def Areaset(width: str, height: str, bcor: str | None = None) -> TeX:
    if bcor is None:
        return ControlSequence("areaset", (Parameter(width), Parameter(height)))
    return ControlSequence(
        "areaset",
        (Parameter(bcor, optional=True), Parameter(width), Parameter(height)),
    )


@Registry.add
@with_package(TYPEAREA)
def Typearea(divisor: int | str) -> TeX:
    return ControlSequence("typearea", (Parameter(str(divisor)),))


@Registry.add
@with_package(TYPEAREA)
def Recalctypearea() -> TeX:
    return ControlSequence("recalctypearea", ())


@Registry.add
@with_package(SCRLAYER_SCRPAGE)
def Pagestyle(name: str) -> TeX:
    return ControlSequence("pagestyle", (Parameter(name),))


@Registry.add
@with_package(SCRLAYER_SCRPAGE)
def Clearpairofpagestyles() -> TeX:
    return ControlSequence("clearpairofpagestyles", ())


@Registry.add
@with_package(SCRLAYER_SCRPAGE)
def Clearscrheadfoot() -> TeX:
    return ControlSequence("clearscrheadfoot", ())


@Registry.add
@with_package(SCRLAYER_SCRPAGE)
def Automark(level: str, second: str | None = None) -> TeX:
    if second is None:
        return ControlSequence("automark", (Parameter(level),))
    return ControlSequence(
        "automark",
        (Parameter(second, optional=True), Parameter(level)),
    )


def _scoped_head_foot(name: str, scope: str | None, body: TeX | str) -> TeX:
    if scope is None:
        return ControlSequence(name, (Parameter(body),))
    return ControlSequence(name, (Parameter(scope, optional=True), Parameter(body)))


@Registry.add
@with_package(SCRLAYER_SCRPAGE)
def Ihead(body: TeX | str, scope: str | None = None) -> TeX:
    return _scoped_head_foot("ihead", scope, body)


@Registry.add
@with_package(SCRLAYER_SCRPAGE)
def Chead(body: TeX | str, scope: str | None = None) -> TeX:
    return _scoped_head_foot("chead", scope, body)


@Registry.add
@with_package(SCRLAYER_SCRPAGE)
def Ohead(body: TeX | str, scope: str | None = None) -> TeX:
    return _scoped_head_foot("ohead", scope, body)


@Registry.add
@with_package(SCRLAYER_SCRPAGE)
def Ifoot(body: TeX | str, scope: str | None = None) -> TeX:
    return _scoped_head_foot("ifoot", scope, body)


@Registry.add
@with_package(SCRLAYER_SCRPAGE)
def Cfoot(body: TeX | str, scope: str | None = None) -> TeX:
    return _scoped_head_foot("cfoot", scope, body)


@Registry.add
@with_package(SCRLAYER_SCRPAGE)
def Ofoot(body: TeX | str, scope: str | None = None) -> TeX:
    return _scoped_head_foot("ofoot", scope, body)
