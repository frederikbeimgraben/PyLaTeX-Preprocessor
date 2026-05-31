# pyright: reportArgumentType=false, reportUntypedFunctionDecorator=false
import pytest

from pytex.registry import Registry


def test_add_returns_obj():
    def MyFunc():
        return None

    assert Registry.add(MyFunc) is MyFunc


def test_add_registers():
    @Registry.add
    def UniqueRegFn():
        return None

    assert Registry.has("UniqueRegFn")
    assert Registry.get("UniqueRegFn") is UniqueRegFn


def test_add_requires_name():
    with pytest.raises((TypeError, AttributeError)):
        Registry.add(object())  # type: ignore[arg-type]


def test_namespace_is_copy():
    ns = Registry.namespace()
    ns["nope"] = None
    assert not Registry.has("nope")


def test_names_contains_known():
    names = Registry.names()
    for n in ("Concat", "Document", "Raw", "Section", "Frac"):
        assert n in names, f"{n} not in registry"


def test_get_unknown_raises():
    with pytest.raises(KeyError):
        Registry.get("definitely_not_here_xyz")
