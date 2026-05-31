from pytex.helpers.with_package import WithPackage, coerce_package, with_package
from pytex.interface.tex import TeX
from pytex.model.control_sequence import ControlSequence
from pytex.model.package import Package
from pytex.packages import AMSMATH


def test_coerce_package_str():
    p = coerce_package("foo_test_pkg")
    assert isinstance(p, Package)
    assert p.name == "foo_test_pkg"


def test_coerce_package_passthrough():
    assert coerce_package(AMSMATH) is AMSMATH


def test_with_package_wraps_result():
    @with_package(AMSMATH)
    def Foo() -> TeX:
        return ControlSequence("foo", ())

    out = Foo()
    assert isinstance(out, WithPackage)
    assert out.rendered == r"\foo"
    assert AMSMATH in out.requires


def test_with_package_preserves_name():
    @with_package(AMSMATH)
    def MyHelper() -> TeX:
        return ControlSequence("x", ())

    assert MyHelper.__name__ == "MyHelper"


def test_with_package_children_descend():
    @with_package(AMSMATH)
    def Bar() -> TeX:
        return ControlSequence("bar", ())

    wp = Bar()
    assert wp.children == (wp.child,)
