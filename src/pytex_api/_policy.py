"""Trust level -> concrete capability policy.

A `TrustPolicy` flattens a `TrustLevel` into the separate gates that the
pipeline checks. The gates cover code execution, `eval` comments, inline
`pytex(...)` markers, shell-escape, the network, the package allowlist, and
the resource limits. The central mapping puts every gate decision where an
auditor can read it.
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

# The packages that PyTeX itself requires, collected from the first-party node
# trees, plus common render-only LaTeX packages with no code-execution surface
# and no file-write surface. Untrusted input may use only this set.
PACKAGE_ALLOWLIST: frozenset[str] = frozenset(
    {
        # -- required by first-party PyTeX nodes and variants --
        "amsmath",
        "array",
        "babel",
        "biblatex",
        "booktabs",
        "calc",
        "cleveref",
        "csquotes",
        "etoolbox",
        # eurosym carries its own euro glyph, so `\euro{}` renders under a
        # font that has none, for example DIN. The Markdown converter uses
        # `\euro{}` for the `€` character.
        "eurosym",
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
        # -- common, safe packages for typography and layout --
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

# The packages that a `sandboxed` build may also use. The set still holds
# nothing that can run code or escape the temporary work directory.
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

# The packages that can run shell commands, run code, or read and write any
# file. PyTeX refuses them for every non-trusted build, whatever the package
# allowlist holds. The allowlist alone already excludes them. This set names
# them, so the error text is explicit. The rule also survives a careless
# widening of the allowlist.
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
    """The concrete gates that one build may pass."""

    level: TrustLevel
    allow_python_exec: bool  # `exec_module` on a `.py` or `.tex.py` file
    allow_markdown_eval: bool  # `[//]: # "EXPR"` comments
    allow_tex_replacements: bool  # `\iffalse{pytex(...)}\fi` markers
    allow_shell_escape: bool  # tectonic `-Z shell-escape` and `\write18`
    allow_network: bool  # the tectonic bundle and the biber download
    enforce_package_allowlist: bool
    apply_rlimits: bool
    # Refuse to compile a PDF when the Podman sandbox is not available,
    # instead of a downgrade to the in-process floor. That floor does not
    # block `\input` or `\openin` of host files. Non-trusted input fails
    # closed.
    require_sandbox: bool
    package_allowlist: frozenset[str]


def policy_for(level: TrustLevel) -> TrustPolicy:
    """Return the capability policy for `level`.

    Returns:
        The `TrustPolicy` with every gate set for the given trust level. The
        `trusted` policy has an empty package allowlist, because it does not
        apply the allowlist at all.
    """
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
            require_sandbox=False,
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
            require_sandbox=True,
            package_allowlist=PACKAGE_ALLOWLIST | SANDBOXED_EXTRA_PACKAGES,
        )
    # `untrusted` is the strict default.
    return TrustPolicy(
        level=level,
        allow_python_exec=False,
        allow_markdown_eval=False,
        allow_tex_replacements=False,
        allow_shell_escape=False,
        allow_network=False,
        enforce_package_allowlist=True,
        apply_rlimits=True,
        require_sandbox=True,
        package_allowlist=PACKAGE_ALLOWLIST,
    )
