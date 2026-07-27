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


def test_fill_keys_are_disjoint():
    # Two modules define `\fill`. In `pytex.commands.lengths` it is a rubber
    # length. In `pytex_tikz` it is a TikZ path command. Each definition needs
    # its own registry key. The reverse lookup then gives the same result for
    # every import order.
    import pytex.commands.lengths as lengths
    import pytex_tikz.tikz as tikz

    assert Registry.get("Fill") is tikz.Fill
    assert Registry.get("Fill_len") is lengths.Fill_len
    assert Registry.get("Fill") is not Registry.get("Fill_len")


def test_lengths_fill_deprecated_alias():
    import pytex.commands.lengths as lengths

    with pytest.warns(DeprecationWarning, match="renamed to Fill_len"):
        alias = lengths.Fill  # type: ignore[attr-defined]
    assert alias is lengths.Fill_len


def test_no_duplicate_fill_key_on_fresh_import():
    # A fresh interpreter that imports both modules must not report a duplicate
    # registry key for `Fill`. The registry writes that warning to stderr.
    import os
    import subprocess
    import sys

    code = (
        "import pytex.commands.lengths\n"
        "import pytex_tikz.tikz\n"
        "from pytex.registry import Registry\n"
        "assert Registry.get('Fill') is pytex_tikz.tikz.Fill\n"
        "assert Registry.get('Fill_len') is pytex.commands.lengths.Fill_len\n"
    )
    result = subprocess.run(
        [sys.executable, "-c", code],
        capture_output=True,
        text=True,
        check=False,
        env={**os.environ, "PYTHONPATH": os.pathsep.join(sys.path)},
    )
    assert result.returncode == 0, result.stderr
    assert "Duplicate key in registry (overwritten): Fill" not in result.stderr
