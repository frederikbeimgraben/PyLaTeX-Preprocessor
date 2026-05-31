from ..helpers.with_package import with_package
from ..interface.tex import TeX
from ..model.control_sequence import ControlSequence, Parameter
from ..model.environment import Environment
from ..packages import BOOKTABS, LONGTABLE, MULTIROW, TABULARX
from ..registry import Registry


@Registry.add
def Tabular(spec: str, body: TeX | str) -> TeX:
    return Environment("tabular", body, (Parameter(spec),))


@Registry.add
@with_package(TABULARX)
def Tabularx(width: str, spec: str, body: TeX | str) -> TeX:
    return Environment("tabularx", body, (Parameter(width), Parameter(spec)))


@Registry.add
@with_package(LONGTABLE)
def Longtable(spec: str, body: TeX | str) -> TeX:
    return Environment("longtable", body, (Parameter(spec),))


@Registry.add
def Multicolumn(cols: int, align: str, body: TeX | str) -> TeX:
    return ControlSequence(
        "multicolumn",
        (Parameter(str(cols)), Parameter(align), Parameter(body)),
    )


@Registry.add
@with_package(MULTIROW)
def Multirow(rows: int, width: str, body: TeX | str) -> TeX:
    return ControlSequence(
        "multirow",
        (Parameter(str(rows)), Parameter(width), Parameter(body)),
    )


@Registry.add
def Hline() -> TeX:
    return ControlSequence("hline", ())


@Registry.add
def Cline(spec: str) -> TeX:
    return ControlSequence("cline", (Parameter(spec),))


@Registry.add
@with_package(BOOKTABS)
def Toprule() -> TeX:
    return ControlSequence("toprule", ())


@Registry.add
@with_package(BOOKTABS)
def Midrule() -> TeX:
    return ControlSequence("midrule", ())


@Registry.add
@with_package(BOOKTABS)
def Bottomrule() -> TeX:
    return ControlSequence("bottomrule", ())


@Registry.add
@with_package(BOOKTABS)
def Cmidrule(spec: str, trim: str | None = None) -> TeX:
    if trim is None:
        return ControlSequence("cmidrule", (Parameter(spec),))
    return ControlSequence(
        "cmidrule",
        (Parameter(trim, optional=True), Parameter(spec)),
    )


@Registry.add
def Arraybackslash() -> TeX:
    return ControlSequence("arraybackslash", ())


@Registry.add
def Arraystretch(factor: str) -> TeX:
    return ControlSequence("arraystretch", (Parameter(factor),))


@Registry.add
def Newcolumntype(name: str, arity: int | None, spec: str) -> TeX:
    if arity is None:
        return ControlSequence(
            "newcolumntype",
            (Parameter(name), Parameter(spec)),
        )
    return ControlSequence(
        "newcolumntype",
        (
            Parameter(name),
            Parameter(str(arity), optional=True),
            Parameter(spec),
        ),
    )
