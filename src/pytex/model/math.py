from ..helpers.with_package import with_package
from ..interface.tex import TeX
from ..packages import AMSFONTS, AMSMATH
from .concat import Concat
from .control_sequence import ControlSequence, Parameter
from .environment import Environment
from .raw import Raw


def Math(body: TeX | str) -> TeX:
    return Concat(
        ControlSequence("(", ()),
        body,
        ControlSequence(")", ()),
    )


def DisplayMath(body: TeX | str) -> TeX:
    return Concat(
        ControlSequence("[", ()),
        body,
        ControlSequence("]", ()),
    )


def Equation(body: TeX | str) -> TeX:
    return Environment("equation", body)


def EquationStar(body: TeX | str) -> TeX:
    return Environment("equation*", body)


@with_package(AMSMATH)
def Align(body: TeX | str) -> TeX:
    return Environment("align", body)


@with_package(AMSMATH)
def AlignStar(body: TeX | str) -> TeX:
    return Environment("align*", body)


@with_package(AMSMATH)
def Gather(body: TeX | str) -> TeX:
    return Environment("gather", body)


@with_package(AMSMATH)
def GatherStar(body: TeX | str) -> TeX:
    return Environment("gather*", body)


@with_package(AMSMATH)
def Multline(body: TeX | str) -> TeX:
    return Environment("multline", body)


@with_package(AMSMATH)
def Split(body: TeX | str) -> TeX:
    return Environment("split", body)


@with_package(AMSMATH)
def Cases(body: TeX | str) -> TeX:
    return Environment("cases", body)


def _matrix(kind: str, rows: list[list[TeX | str]]) -> TeX:
    body_str = " \\\\ ".join(" & ".join(str(c) for c in row) for row in rows)
    return Environment(kind, Raw(body_str))


@with_package(AMSMATH)
def Matrix(rows: list[list[TeX | str]]) -> TeX:
    return _matrix("matrix", rows)


@with_package(AMSMATH)
def Pmatrix(rows: list[list[TeX | str]]) -> TeX:
    return _matrix("pmatrix", rows)


@with_package(AMSMATH)
def Bmatrix(rows: list[list[TeX | str]]) -> TeX:
    return _matrix("bmatrix", rows)


@with_package(AMSMATH)
def Vmatrix(rows: list[list[TeX | str]]) -> TeX:
    return _matrix("vmatrix", rows)


@with_package(AMSMATH)
def BBmatrix(rows: list[list[TeX | str]]) -> TeX:
    return _matrix("Bmatrix", rows)


@with_package(AMSMATH)
def VVmatrix(rows: list[list[TeX | str]]) -> TeX:
    return _matrix("Vmatrix", rows)


def Frac(num: TeX | str, den: TeX | str) -> TeX:
    return ControlSequence("frac", (Parameter(num), Parameter(den)))


@with_package(AMSMATH)
def Dfrac(num: TeX | str, den: TeX | str) -> TeX:
    return ControlSequence("dfrac", (Parameter(num), Parameter(den)))


@with_package(AMSMATH)
def Tfrac(num: TeX | str, den: TeX | str) -> TeX:
    return ControlSequence("tfrac", (Parameter(num), Parameter(den)))


@with_package(AMSMATH)
def Binom(top: TeX | str, bot: TeX | str) -> TeX:
    return ControlSequence("binom", (Parameter(top), Parameter(bot)))


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


def Sub(base: TeX | str, sub: TeX | str) -> TeX:
    return _sub_super(base if isinstance(base, TeX) else Raw(base), sub, None)


def Super(base: TeX | str, sup: TeX | str) -> TeX:
    return _sub_super(base if isinstance(base, TeX) else Raw(base), None, sup)


def SubSuper(base: TeX | str, sub: TeX | str, sup: TeX | str) -> TeX:
    return _sub_super(base if isinstance(base, TeX) else Raw(base), sub, sup)


def Sum(lower: TeX | str | None = None, upper: TeX | str | None = None) -> TeX:
    return _sub_super(ControlSequence("sum", ()), lower, upper)


def Prod(lower: TeX | str | None = None, upper: TeX | str | None = None) -> TeX:
    return _sub_super(ControlSequence("prod", ()), lower, upper)


def Int(lower: TeX | str | None = None, upper: TeX | str | None = None) -> TeX:
    return _sub_super(ControlSequence("int", ()), lower, upper)


def OInt(lower: TeX | str | None = None, upper: TeX | str | None = None) -> TeX:
    return _sub_super(ControlSequence("oint", ()), lower, upper)


@with_package(AMSMATH)
def IInt(lower: TeX | str | None = None, upper: TeX | str | None = None) -> TeX:
    return _sub_super(ControlSequence("iint", ()), lower, upper)


@with_package(AMSMATH)
def IIInt(lower: TeX | str | None = None, upper: TeX | str | None = None) -> TeX:
    return _sub_super(ControlSequence("iiint", ()), lower, upper)


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


@with_package(AMSMATH)
def Text(body: TeX | str) -> TeX:
    return ControlSequence("text", (Parameter(body),))


@with_package(AMSFONTS)
def Mathbb(body: TeX | str) -> TeX:
    return ControlSequence("mathbb", (Parameter(body),))


def Mathcal(body: TeX | str) -> TeX:
    return ControlSequence("mathcal", (Parameter(body),))


@with_package(AMSFONTS)
def Mathfrak(body: TeX | str) -> TeX:
    return ControlSequence("mathfrak", (Parameter(body),))


def Mathbf(body: TeX | str) -> TeX:
    return ControlSequence("mathbf", (Parameter(body),))


def Mathit(body: TeX | str) -> TeX:
    return ControlSequence("mathit", (Parameter(body),))


def Mathrm(body: TeX | str) -> TeX:
    return ControlSequence("mathrm", (Parameter(body),))


def Mathsf(body: TeX | str) -> TeX:
    return ControlSequence("mathsf", (Parameter(body),))


def Mathtt(body: TeX | str) -> TeX:
    return ControlSequence("mathtt", (Parameter(body),))


def Overline(body: TeX | str) -> TeX:
    return ControlSequence("overline", (Parameter(body),))


def Underline(body: TeX | str) -> TeX:
    return ControlSequence("underline", (Parameter(body),))


def Overbrace(body: TeX | str) -> TeX:
    return ControlSequence("overbrace", (Parameter(body),))


def Underbrace(body: TeX | str) -> TeX:
    return ControlSequence("underbrace", (Parameter(body),))


def Hat(body: TeX | str) -> TeX:
    return ControlSequence("hat", (Parameter(body),))


def Tilde(body: TeX | str) -> TeX:
    return ControlSequence("tilde", (Parameter(body),))


def Bar(body: TeX | str) -> TeX:
    return ControlSequence("bar", (Parameter(body),))


def Vec(body: TeX | str) -> TeX:
    return ControlSequence("vec", (Parameter(body),))


def Dot(body: TeX | str) -> TeX:
    return ControlSequence("dot", (Parameter(body),))


def Ddot(body: TeX | str) -> TeX:
    return ControlSequence("ddot", (Parameter(body),))


def Label(name: str) -> TeX:
    return ControlSequence("label", (Parameter(name),))


@with_package(AMSMATH)
def Eqref(name: str) -> TeX:
    return ControlSequence("eqref", (Parameter(name),))


@with_package(AMSMATH)
def Operatorname(name: str) -> TeX:
    return ControlSequence("operatorname", (Parameter(name),))


@with_package(AMSMATH)
def Substack(body: TeX | str) -> TeX:
    return ControlSequence("substack", (Parameter(body),))
