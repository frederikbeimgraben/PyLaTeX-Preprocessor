from ..helpers.with_package import with_package
from ..interface.tex import TeX
from ..packages import AMSFONTS, AMSMATH
from ..registry import Registry
from .concat import Concat
from .control_sequence import ControlSequence, Parameter
from .environment import Environment
from .raw import Raw

__all__ = [
    "Align",
    "AlignStar",
    "BBmatrix",
    "Bar",
    "Binom",
    "Bmatrix",
    "Cases",
    "Ddot",
    "Dfrac",
    "DisplayMath",
    "Dot",
    "Eqref",
    "Equation",
    "EquationStar",
    "Frac",
    "Gather",
    "GatherStar",
    "Hat",
    "IIInt",
    "IInt",
    "Int",
    "LabelM",
    "Lim",
    "Math",
    "Mathbb",
    "Mathbf",
    "Mathcal",
    "Mathfrak",
    "Mathit",
    "Mathrm",
    "Mathsf",
    "Mathtt",
    "Matrix",
    "Multline",
    "OInt",
    "Operatorname",
    "Overbrace",
    "Overline",
    "Pmatrix",
    "Prod",
    "Split",
    "Sqrt",
    "Sub",
    "SubSuper",
    "Substack",
    "Sum",
    "Super",
    "Text",
    "Tfrac",
    "Tilde",
    "Underbrace",
    "UnderlineM",
    "VVmatrix",
    "Vec",
    "Vmatrix",
]


@Registry.add
def Math(body: TeX | str) -> TeX:
    return Concat(
        ControlSequence("(", ()),
        body,
        ControlSequence(")", ()),
    )


@Registry.add
def DisplayMath(body: TeX | str) -> TeX:
    return Concat(
        ControlSequence("[", ()),
        body,
        ControlSequence("]", ()),
    )


@Registry.add
def Equation(body: TeX | str) -> TeX:
    return Environment("equation", body)


@Registry.add
def EquationStar(body: TeX | str) -> TeX:
    return Environment("equation*", body)


@Registry.add
@with_package(AMSMATH)
def Align(body: TeX | str) -> TeX:
    return Environment("align", body)


@Registry.add
@with_package(AMSMATH)
def AlignStar(body: TeX | str) -> TeX:
    return Environment("align*", body)


@Registry.add
@with_package(AMSMATH)
def Gather(body: TeX | str) -> TeX:
    return Environment("gather", body)


@Registry.add
@with_package(AMSMATH)
def GatherStar(body: TeX | str) -> TeX:
    return Environment("gather*", body)


@Registry.add
@with_package(AMSMATH)
def Multline(body: TeX | str) -> TeX:
    return Environment("multline", body)


@Registry.add
@with_package(AMSMATH)
def Split(body: TeX | str) -> TeX:
    return Environment("split", body)


@Registry.add
@with_package(AMSMATH)
def Cases(body: TeX | str) -> TeX:
    return Environment("cases", body)


def _matrix(kind: str, rows: list[list[TeX | str]]) -> TeX:
    body_str = " \\\\ ".join(" & ".join(str(c) for c in row) for row in rows)
    return Environment(kind, Raw(body_str))


@Registry.add
@with_package(AMSMATH)
def Matrix(rows: list[list[TeX | str]]) -> TeX:
    return _matrix("matrix", rows)


@Registry.add
@with_package(AMSMATH)
def Pmatrix(rows: list[list[TeX | str]]) -> TeX:
    return _matrix("pmatrix", rows)


@Registry.add
@with_package(AMSMATH)
def Bmatrix(rows: list[list[TeX | str]]) -> TeX:
    return _matrix("bmatrix", rows)


@Registry.add
@with_package(AMSMATH)
def Vmatrix(rows: list[list[TeX | str]]) -> TeX:
    return _matrix("vmatrix", rows)


@Registry.add
@with_package(AMSMATH)
def BBmatrix(rows: list[list[TeX | str]]) -> TeX:
    return _matrix("Bmatrix", rows)


@Registry.add
@with_package(AMSMATH)
def VVmatrix(rows: list[list[TeX | str]]) -> TeX:
    return _matrix("Vmatrix", rows)


@Registry.add
def Frac(num: TeX | str, den: TeX | str) -> TeX:
    return ControlSequence("frac", (Parameter(num), Parameter(den)))


@Registry.add
@with_package(AMSMATH)
def Dfrac(num: TeX | str, den: TeX | str) -> TeX:
    return ControlSequence("dfrac", (Parameter(num), Parameter(den)))


@Registry.add
@with_package(AMSMATH)
def Tfrac(num: TeX | str, den: TeX | str) -> TeX:
    return ControlSequence("tfrac", (Parameter(num), Parameter(den)))


@Registry.add
@with_package(AMSMATH)
def Binom(top: TeX | str, bot: TeX | str) -> TeX:
    return ControlSequence("binom", (Parameter(top), Parameter(bot)))


@Registry.add
def Sqrt(body: TeX | str, n: TeX | str | None = None) -> TeX:
    if n is None:
        return ControlSequence("sqrt", (Parameter(body),))
    return ControlSequence("sqrt", (Parameter(n, optional=True), Parameter(body)))


def _sub_super(base: TeX, sub: TeX | str | None, sup: TeX | str | None) -> TeX:
    parts: list[TeX | str] = [base]
    if sub is not None:
        parts.append(Raw("_{"))
        parts.append(sub)
        parts.append(Raw("}"))
    if sup is not None:
        parts.append(Raw("^{"))
        parts.append(sup)
        parts.append(Raw("}"))
    return Concat(*parts)


@Registry.add
def Sub(base: TeX | str, sub: TeX | str) -> TeX:
    return _sub_super(base if isinstance(base, TeX) else Raw(base), sub, None)


@Registry.add
def Super(base: TeX | str, sup: TeX | str) -> TeX:
    return _sub_super(base if isinstance(base, TeX) else Raw(base), None, sup)


@Registry.add
def SubSuper(base: TeX | str, sub: TeX | str, sup: TeX | str) -> TeX:
    return _sub_super(base if isinstance(base, TeX) else Raw(base), sub, sup)


@Registry.add
def Sum(lower: TeX | str | None = None, upper: TeX | str | None = None) -> TeX:
    return _sub_super(ControlSequence("sum", ()), lower, upper)


@Registry.add
def Prod(lower: TeX | str | None = None, upper: TeX | str | None = None) -> TeX:
    return _sub_super(ControlSequence("prod", ()), lower, upper)


@Registry.add
def Int(lower: TeX | str | None = None, upper: TeX | str | None = None) -> TeX:
    return _sub_super(ControlSequence("int", ()), lower, upper)


@Registry.add
def OInt(lower: TeX | str | None = None, upper: TeX | str | None = None) -> TeX:
    return _sub_super(ControlSequence("oint", ()), lower, upper)


@Registry.add
@with_package(AMSMATH)
def IInt(lower: TeX | str | None = None, upper: TeX | str | None = None) -> TeX:
    return _sub_super(ControlSequence("iint", ()), lower, upper)


@Registry.add
@with_package(AMSMATH)
def IIInt(lower: TeX | str | None = None, upper: TeX | str | None = None) -> TeX:
    return _sub_super(ControlSequence("iiint", ()), lower, upper)


@Registry.add
def Lim(var: TeX | str, to: TeX | str) -> TeX:
    return _sub_super(
        ControlSequence("lim", ()),
        Concat(
            var if isinstance(var, TeX) else Raw(var),
            Raw(" \\to "),
            to if isinstance(to, TeX) else Raw(to),
        ),
        None,
    )


@Registry.add
@with_package(AMSMATH)
def Text(body: TeX | str) -> TeX:
    return ControlSequence("text", (Parameter(body),))


@Registry.add
@with_package(AMSFONTS)
def Mathbb(body: TeX | str) -> TeX:
    return ControlSequence("mathbb", (Parameter(body),))


@Registry.add
def Mathcal(body: TeX | str) -> TeX:
    return ControlSequence("mathcal", (Parameter(body),))


@Registry.add
@with_package(AMSFONTS)
def Mathfrak(body: TeX | str) -> TeX:
    return ControlSequence("mathfrak", (Parameter(body),))


@Registry.add
def Mathbf(body: TeX | str) -> TeX:
    return ControlSequence("mathbf", (Parameter(body),))


@Registry.add
def Mathit(body: TeX | str) -> TeX:
    return ControlSequence("mathit", (Parameter(body),))


@Registry.add
def Mathrm(body: TeX | str) -> TeX:
    return ControlSequence("mathrm", (Parameter(body),))


@Registry.add
def Mathsf(body: TeX | str) -> TeX:
    return ControlSequence("mathsf", (Parameter(body),))


@Registry.add
def Mathtt(body: TeX | str) -> TeX:
    return ControlSequence("mathtt", (Parameter(body),))


@Registry.add
def Overline(body: TeX | str) -> TeX:
    return ControlSequence("overline", (Parameter(body),))


@Registry.add
def UnderlineM(body: TeX | str) -> TeX:
    return ControlSequence("underline", (Parameter(body),))


@Registry.add
def Overbrace(body: TeX | str) -> TeX:
    return ControlSequence("overbrace", (Parameter(body),))


@Registry.add
def Underbrace(body: TeX | str) -> TeX:
    return ControlSequence("underbrace", (Parameter(body),))


@Registry.add
def Hat(body: TeX | str) -> TeX:
    return ControlSequence("hat", (Parameter(body),))


@Registry.add
def Tilde(body: TeX | str) -> TeX:
    return ControlSequence("tilde", (Parameter(body),))


@Registry.add
def Bar(body: TeX | str) -> TeX:
    return ControlSequence("bar", (Parameter(body),))


@Registry.add
def Vec(body: TeX | str) -> TeX:
    return ControlSequence("vec", (Parameter(body),))


@Registry.add
def Dot(body: TeX | str) -> TeX:
    return ControlSequence("dot", (Parameter(body),))


@Registry.add
def Ddot(body: TeX | str) -> TeX:
    return ControlSequence("ddot", (Parameter(body),))


@Registry.add
def LabelM(name: str) -> TeX:
    return ControlSequence("label", (Parameter(name),))


@Registry.add
@with_package(AMSMATH)
def Eqref(name: str) -> TeX:
    return ControlSequence("eqref", (Parameter(name),))


@Registry.add
@with_package(AMSMATH)
def Operatorname(name: str) -> TeX:
    return ControlSequence("operatorname", (Parameter(name),))


@Registry.add
@with_package(AMSMATH)
def Substack(body: TeX | str) -> TeX:
    return ControlSequence("substack", (Parameter(body),))
