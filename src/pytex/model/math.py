from pytex.interface.package import PackageProtocol

from ..interface.tex import TeX
from .concat import Concat
from .control_sequence import ControlSequence, Parameter
from .environment import Begin, End
from .package import DefinePackage
from .raw import Raw

amsmath = DefinePackage("amsmath")
amssymb = DefinePackage("amssymb")
amsfonts = DefinePackage("amsfonts")
mathtools = DefinePackage("mathtools")


def _env_with_packages(
    name: str, body: TeX | str, packages: frozenset[PackageProtocol]
) -> TeX:
    return Concat(
        ControlSequence("begin", (Parameter(Raw(name)),), required_packages=packages),
        body,
        End(name),
    )


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
    return Concat(Begin("equation"), body, End("equation"))


def EquationStar(body: TeX | str) -> TeX:
    return Concat(Begin("equation*"), body, End("equation*"))


def Align(body: TeX | str) -> TeX:
    return _env_with_packages("align", body, frozenset({amsmath}))


def AlignStar(body: TeX | str) -> TeX:
    return _env_with_packages("align*", body, frozenset({amsmath}))


def Gather(body: TeX | str) -> TeX:
    return _env_with_packages("gather", body, frozenset({amsmath}))


def GatherStar(body: TeX | str) -> TeX:
    return _env_with_packages("gather*", body, frozenset({amsmath}))


def Multline(body: TeX | str) -> TeX:
    return _env_with_packages("multline", body, frozenset({amsmath}))


def Split(body: TeX | str) -> TeX:
    return _env_with_packages("split", body, frozenset({amsmath}))


def Cases(body: TeX | str) -> TeX:
    return _env_with_packages("cases", body, frozenset({amsmath}))


def _matrix(kind: str, rows: list[list[TeX | str]]) -> TeX:
    body_str = " \\\\ ".join(" & ".join(str(c) for c in row) for row in rows)
    return _env_with_packages(kind, Raw(body_str), frozenset({amsmath}))


def Matrix(rows: list[list[TeX | str]]) -> TeX:
    return _matrix("matrix", rows)


def Pmatrix(rows: list[list[TeX | str]]) -> TeX:
    return _matrix("pmatrix", rows)


def Bmatrix(rows: list[list[TeX | str]]) -> TeX:
    return _matrix("bmatrix", rows)


def Vmatrix(rows: list[list[TeX | str]]) -> TeX:
    return _matrix("vmatrix", rows)


def BBmatrix(rows: list[list[TeX | str]]) -> TeX:
    return _matrix("Bmatrix", rows)


def VVmatrix(rows: list[list[TeX | str]]) -> TeX:
    return _matrix("Vmatrix", rows)


def Frac(num: TeX | str, den: TeX | str) -> TeX:
    return ControlSequence("frac", (Parameter(num), Parameter(den)))


def Dfrac(num: TeX | str, den: TeX | str) -> TeX:
    return ControlSequence(
        "dfrac",
        (Parameter(num), Parameter(den)),
        required_packages=frozenset({amsmath}),
    )


def Tfrac(num: TeX | str, den: TeX | str) -> TeX:
    return ControlSequence(
        "tfrac",
        (Parameter(num), Parameter(den)),
        required_packages=frozenset({amsmath}),
    )


def Binom(top: TeX | str, bot: TeX | str) -> TeX:
    return ControlSequence(
        "binom",
        (Parameter(top), Parameter(bot)),
        required_packages=frozenset({amsmath}),
    )


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


def Text(body: TeX | str) -> TeX:
    return ControlSequence(
        "text",
        (Parameter(body),),
        required_packages=frozenset({amsmath}),
    )


def Mathbb(body: TeX | str) -> TeX:
    return ControlSequence(
        "mathbb",
        (Parameter(body),),
        required_packages=frozenset({amsfonts}),
    )


def Mathcal(body: TeX | str) -> TeX:
    return ControlSequence("mathcal", (Parameter(body),))


def Mathfrak(body: TeX | str) -> TeX:
    return ControlSequence(
        "mathfrak",
        (Parameter(body),),
        required_packages=frozenset({amsfonts}),
    )


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


def Eqref(name: str) -> TeX:
    return ControlSequence(
        "eqref",
        (Parameter(name),),
        required_packages=frozenset({amsmath}),
    )
