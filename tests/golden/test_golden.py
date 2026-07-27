"""Golden-file regression tests for the render layer.

Each sample input is a Markdown file or one `.tex.py` file. The test renders
the input to a LaTeX string in memory. It runs no tectonic binary, it makes no
PDF, and it starts no subprocess. The test then compares the string
byte-for-byte with a golden file under `tests/golden/expected/`. A difference
fails the test, so a later refactor cannot change the render output in silence.

To rewrite every golden from the current render, set `PYTEX_UPDATE_GOLDEN=1`:

    PYTEX_UPDATE_GOLDEN=1 pytest tests/golden -q

Read the resulting diff before you commit. An intended change of the render
output appears there. An accidental change is the regression that this suite
must catch.

The render layer has no timestamps, no randomness, and no counters that depend
on set order or dict order. The one machine-dependent source is
`Path.resolve()` on a relative image path or logo path. The samples avoid such
a path. They use no relative image, and they name vendored logos only.
`_normalise` also replaces the absolute path of the worktree. A leaked path
then becomes a stable token, and the golden stays the same on every machine.
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
    """One golden case: an input file, a variant, and a golden file name.

    Attributes:
        name: The stem of the golden file under `tests/golden/expected/`.
        source: The file name under `tests/golden/inputs/`.
        variant: The variant for a Markdown input. It is None for a `.tex.py`
            file, because such a file takes no variant.
    """

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
    """Replace a machine-specific absolute path with a stable token.

    The samples avoid path leakage, so this function usually changes nothing.
    It keeps the golden stable if a later code path starts to render an
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
