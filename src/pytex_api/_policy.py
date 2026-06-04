"""Trust-level -> concrete capability policy.

A :class:`TrustPolicy` flattens a :class:`TrustLevel` into the individual
gates the pipeline checks: code execution, eval comments, ``.tex`` replacements,
shell-escape, network, the package allowlist, and resource limits. Centralising
the mapping keeps the gating decisions in one auditable place.
"""

from __future__ import annotations

from dataclasses import dataclass

from ._models import TrustLevel

__all__ = [
    "DANGEROUS_PACKAGES",
    "PACKAGE_ALLOWLIST",
    "SANDBOXED_EXTRA_PACKAGES",
    "TrustPolicy",
    "policy_for",
]

# Packages PyTeX itself emits (collected from the first-party node trees) plus
# common, render-only LaTeX packages with no code-execution or file-write
# surface. Untrusted input may only pull packages from this set.
PACKAGE_ALLOWLIST: frozenset[str] = frozenset(
    {
        # -- emitted by first-party PyTeX nodes/variants --
        "amsmath",
        "array",
        "babel",
        "biblatex",
        "booktabs",
        "calc",
        "cleveref",
        "csquotes",
        "etoolbox",
        "fontawesome",
        "fontspec",
        "geometry",
        "glossaries",
        "graphicx",
        "hyperref",
        "lastpage",
        "listings",
        "lmodern",
        "longtable",
        "mdframed",
        "needspace",
        "pgf",
        "pgffor",
        "ragged2e",
        "scrlayer-scrpage",
        "setspace",
        "tabularx",
        "tikz",
        "xcolor",
        # -- common, safe typographic/layout packages --
        "amssymb",
        "amsfonts",
        "mathtools",
        "enumitem",
        "microtype",
        "parskip",
        "fancyhdr",
        "titlesec",
        "caption",
        "subcaption",
        "float",
        "wrapfig",
        "multirow",
        "multicol",
        "url",
        "xspace",
        "textcomp",
        "ulem",
        "soul",
        "colortbl",
        "tcolorbox",
        "siunitx",
    }
)

# Packages a slightly-more-trusted (SANDBOXED) build may additionally use.
# Still excludes anything that can execute code or escape the workdir.
SANDBOXED_EXTRA_PACKAGES: frozenset[str] = frozenset(
    {
        "pgfplots",
        "circuitikz",
        "forest",
        "tikz-cd",
        "algorithm2e",
        "algorithmicx",
        "algpseudocode",
        "fancyvrb",
        "bytefield",
        "chemfig",
    }
)

# Packages that can execute shell commands, run code, or read/write arbitrary
# files. Rejected for any non-TRUSTED build regardless of the allowlist - the
# allowlist is exclusive, but these are named so the error is explicit and so
# the rule survives someone widening the allowlist by accident.
DANGEROUS_PACKAGES: frozenset[str] = frozenset(
    {
        "shellesc",
        "write18",
        "python",
        "pythontex",
        "pyluatex",
        "minted",
        "minted2",
        "catchfile",
        "spawnproc",
        "bashful",
        "texmf",
        "luacode",
        "luaexec",
    }
)


@dataclass(frozen=True)
class TrustPolicy:
    """The concrete gates a single build is allowed to pass."""

    level: TrustLevel
    allow_python_exec: bool  # .py / .tex.py exec_module
    allow_markdown_eval: bool  # [//]: # "EXPR" comments
    allow_tex_replacements: bool  # \iffalse{pytex(...)}\fi
    allow_shell_escape: bool  # tectonic -Z shell-escape / \write18
    allow_network: bool  # tectonic bundle / biber auto-download
    enforce_package_allowlist: bool
    apply_rlimits: bool
    package_allowlist: frozenset[str]


def policy_for(level: TrustLevel) -> TrustPolicy:
    """Return the capability policy for ``level``."""
    if level is TrustLevel.TRUSTED:
        return TrustPolicy(
            level=level,
            allow_python_exec=True,
            allow_markdown_eval=True,
            allow_tex_replacements=True,
            allow_shell_escape=True,
            allow_network=True,
            enforce_package_allowlist=False,
            apply_rlimits=False,
            package_allowlist=frozenset(),
        )
    if level is TrustLevel.SANDBOXED:
        return TrustPolicy(
            level=level,
            allow_python_exec=False,
            allow_markdown_eval=False,
            allow_tex_replacements=False,
            allow_shell_escape=False,
            allow_network=False,
            enforce_package_allowlist=True,
            apply_rlimits=True,
            package_allowlist=PACKAGE_ALLOWLIST | SANDBOXED_EXTRA_PACKAGES,
        )
    # UNTRUSTED - the strict default.
    return TrustPolicy(
        level=level,
        allow_python_exec=False,
        allow_markdown_eval=False,
        allow_tex_replacements=False,
        allow_shell_escape=False,
        allow_network=False,
        enforce_package_allowlist=True,
        apply_rlimits=True,
        package_allowlist=PACKAGE_ALLOWLIST,
    )
