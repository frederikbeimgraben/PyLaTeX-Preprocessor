"""Regression tests for the backlog bugs owned by the model-packages cluster.

Each test reproduces one entry from `docs/bug-backlog.md`. The test name
carries the backlog file and line so a reader can match it back to the entry.
"""

from pytex.helpers.parenting import attach
from pytex.helpers.with_package import WithPackage, coerce_package
from pytex.model.color import Color, collect_colors
from pytex.model.concat import Concat
from pytex.model.document import Document
from pytex.model.empty import Empty
from pytex.model.package import PACKAGES, DefinePackage, Package
from pytex.model.raw import Raw


def test_package_post_init_registers_direct_instance():
    """`Package(...)` alone must register into `PACKAGES`.

    Backlog: src/pytex/model/package.py:84.
    """
    name = "repro_post_init_test_pkg"
    assert name not in PACKAGES
    p = Package(name)
    assert PACKAGES[name] is p


def test_document_packages_expand_after_transitively():
    """A package requirement must pull in its whole `after` chain.

    Backlog: src/pytex/model/document.py:60.
    """
    base = DefinePackage("repro_transitive_base_test")
    mid = DefinePackage("repro_transitive_mid_test", after={base})
    top = DefinePackage("repro_transitive_top_test", after={mid})

    doc = Document(WithPackage(Raw("x"), top))
    assert base in doc.packages


def test_tint_keeps_base_color_definecolor():
    """`tint()` must keep the base color reachable so it still gets defined.

    Backlog: src/pytex/model/color.py:137.
    """
    base = Color.hex("FF00A1")
    tinted = base.tint(20)
    names = {c.name for c in collect_colors(Concat(tinted))}
    assert base.name in names


def test_mix_keeps_both_base_colors_definecolor():
    """`mix()` must keep both base colors reachable for `\\definecolor`.

    Backlog: src/pytex/model/color.py:137.
    """
    a = Color.hex("00FF00")
    b = Color.hex("0000FF")
    mixed = a.mix(b, 30)
    names = {c.name for c in collect_colors(Concat(mixed))}
    assert a.name in names
    assert b.name in names


def test_attach_does_not_write_parent_onto_empty_singleton():
    """`attach()` must not set `_parent` on the shared `Empty` node.

    Backlog: src/pytex/helpers/parenting.py:22.
    """
    doc1 = Document(body="a")
    attach(doc1, Empty)
    assert Empty.parent is None


def test_coerce_package_reuses_registered_instance():
    """`coerce_package` must return the one registered `Package` per name.

    Backlog: src/pytex/helpers/with_package.py:24.
    """
    name = "repro_coerce_reuse_test_pkg"
    registered = DefinePackage(name, after=set())
    coerced = coerce_package(name)
    assert coerced is registered
