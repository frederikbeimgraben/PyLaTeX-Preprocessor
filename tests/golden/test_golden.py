"""Golden-file regression tests for the deterministic ``.tex`` render layer.

Each sample input (Markdown variants plus one ``.tex.py`` node tree) is rendered
to a LaTeX *string* in memory -- no tectonic, no PDF, no subprocess -- and
compared byte-for-byte against a checked-in golden file under
``tests/golden/expected/``. A diff fails the test, freezing the render output so
future refactors cannot silently change it.

Regenerating goldens
--------------------
Set ``PYTEX_UPDATE_GOLDEN=1`` to rewrite every golden from the current render::

    PYTEX_UPDATE_GOLDEN=1 pytest tests/golden -q

Review the resulting diff before committing -- an intended output change shows up
there, an accidental one is the regression this suite is meant to catch.

Determinism
-----------
The render layer has no timestamps, randomness, or counters tied to set/dict
iteration. The one machine-dependent source is ``Path.resolve()`` on relative
image/logo *paths*; the samples avoid those (no relative images; vendored logo
names only). :func:`_normalise` additionally strips the worktree's absolute path
as defence in depth, so a leaked path would surface as a stable token rather than
a flapping golden.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

import pytest

from pytex_builder.render import render_input

_HERE = Path(__file__).resolve().parent
_INPUTS = _HERE / "inputs"
_EXPECTED = _HERE / "expected"
_REPO_ROOT = _HERE.parent.parent

_UPDATE = os.environ.get("PYTEX_UPDATE_GOLDEN") == "1"


@dataclass(frozen=True)
class Case:
    """One golden case: an input file, its render variant, and a golden name."""

    name: str
    source: str
    variant: str | None


CASES: tuple[Case, ...] = (
    Case("plain", "plain.md", "plain"),
    Case("report", "report.md", "report"),
    Case("protocol-asta", "protocol-asta.md", "protocol-asta"),
    Case("protocol-stupa", "protocol-stupa.md", "protocol-stupa"),
    Case("nodetree", "nodetree.tex.py", None),
)


def _normalise(rendered: str) -> str:
    """Replace machine-specific absolute paths with a stable token.

    The samples are written to avoid path leakage, so in practice this is a
    no-op; it keeps the golden stable if a future code path starts emitting an
    absolute path under the worktree.
    """
    return rendered.replace(str(_REPO_ROOT), "<REPO>")


def _render(case: Case) -> str:
    return _normalise(render_input(_INPUTS / case.source, variant=case.variant))


@pytest.mark.parametrize("case", CASES, ids=[case.name for case in CASES])
def test_golden(case: Case) -> None:
    rendered = _render(case)
    golden = _EXPECTED / f"{case.name}.tex"
    if _UPDATE:
        golden.write_text(rendered, encoding="utf-8")
        return
    assert golden.is_file(), (
        f"missing golden {golden.name}; run PYTEX_UPDATE_GOLDEN=1 pytest to create it"
    )
    expected = golden.read_text(encoding="utf-8")
    assert rendered == expected, (
        f"rendered .tex for {case.name!r} differs from golden; "
        "if intended, regenerate with PYTEX_UPDATE_GOLDEN=1 pytest"
    )
