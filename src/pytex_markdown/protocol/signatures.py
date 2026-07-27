"""The signature block that closes a meeting protocol.

The roles are German, for example `Sitzungsleitung` (chair) and
`Schriftführung` (the person who writes the protocol). Each signer gets a
block with a signature rule, the printed name and the role. The blocks sit
side by side, two per row, under an `Unterschriften` (signatures) heading. A
name comes from the frontmatter when the frontmatter holds it. Otherwise the
line stays blank for a hand-written signature.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from pytex.helpers.sanitize import escape_latex
from pytex.model.raw import Raw
from pytex.registry import Registry

if TYPE_CHECKING:
    from collections.abc import Mapping

    from pytex.interface.tex import TeX

    from ..frontmatter import FrontmatterValue

__all__ = ["SignatureLines", "signature_block_from_meta"]

# Role label in lower case -> the frontmatter keys that may hold the name of
# the signer.
_ROLE_NAME_KEYS: dict[str, tuple[str, ...]] = {
    "sitzungsleitung": ("sitzungsleitung",),
    "schriftführung": ("protokoll", "schriftführung", "schriftfuehrung"),
    "schriftfuehrung": ("protokoll", "schriftfuehrung"),
    "protokoll": ("protokoll",),
    "vorstand": ("vorstand",),
}
_RULE_WIDTH = "5cm"


def _cell(role: str, name: str) -> str:
    printed = escape_latex(name) if name else "~"
    return (
        r"\begin{minipage}[t]{0.46\linewidth}\centering"
        + rf"\rule{{{_RULE_WIDTH}}}{{0.4pt}}\\[0.4em]"
        + printed
        + r"\\{\small "
        + escape_latex(role)
        + r"}\end{minipage}"
    )


@Registry.add
def SignatureLines(*signers: tuple[str, str] | str) -> TeX:
    """Signature blocks with a rule, a name and a role, two per row.

    Args:
        signers: One `(role, name)` pair per signer. A bare string is a role
            with a blank line for a hand-written signature.
    """
    pairs = [(s, "") if isinstance(s, str) else s for s in signers]
    if not pairs:
        return Raw("")
    rows = [
        r"\noindent "
        + r"\hfill".join(_cell(role, name) for role, name in pairs[i : i + 2])
        for i in range(0, len(pairs), 2)
    ]
    block = r"\par\vspace{3.5em}".join(rows)
    return Raw(r"\par\vspace{2em}\section*{Unterschriften}\par\vspace{3em}" + block)


def _name_for(role: str, meta: Mapping[str, FrontmatterValue]) -> str:
    key = role.lower().strip()
    for candidate in _ROLE_NAME_KEYS.get(key, (key,)):
        value = meta.get(candidate)
        if isinstance(value, str) and value:
            return value
    return ""


def signature_block_from_meta(meta: Mapping[str, FrontmatterValue]) -> TeX | None:
    """Build a signature block from the `unterschriften` frontmatter list.

    Returns:
        The signature block, or `None` when the key is absent or empty. The
        caller then appends the block only when it exists.
    """
    roles = meta.get("unterschriften")
    if not isinstance(roles, list) or not roles:
        return None
    return SignatureLines(*((str(role), _name_for(str(role), meta)) for role in roles))
