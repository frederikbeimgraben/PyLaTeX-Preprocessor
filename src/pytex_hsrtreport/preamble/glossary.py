"""Glossary style + entry-name overrides — all native.

The original ``\\newcommand{\\acr}{\\acrshort}`` alias is gone — Python
callers use :func:`pytex.acr` directly, so the TeX-side macro is dead code.
"""

from pytex import (
    BeginEnvironment,
    Command,
    EndEnvironment,
    GlsAddKey,
    NewColumnType,
    NewEnvironment,
    NewGlossaryStyle,
    RenewCommand,
    SetGlossaryStyle,
    TeX,
)
from pytex_komascript.model import Block

_GLOSSARY_TABLE_COLS = (
    "@{} L{0.30\\textwidth-\\tabcolsep} "
    "p{0.58\\textwidth-\\tabcolsep} "
    "L{0.10\\textwidth-\\tabcolsep} @{}"
)


def _ColumnTypes() -> TeX:
    """``L``, ``C``, ``R`` paragraph columns from the original style file."""
    common = "\\let\\newline\\\\\\arraybackslash\\hspace{0pt}"
    return Block(
        *(
            NewColumnType(
                letter,
                f">{{\\{align}{common}}}p{{#1}}",
                n_args=1,
            )
            for letter, align in (("L", "raggedright"), ("C", "centering"), ("R", "raggedleft"))
        )
    )


def _ManualFixedWidthStyle() -> TeX:
    return NewGlossaryStyle(
        "manualfixedwidth",
        Block(
            SetGlossaryStyle("long3colheader"),
            NewEnvironment(
                "theglossary",
                BeginEnvironment("longtable", _GLOSSARY_TABLE_COLS),
                EndEnvironment("longtable"),
                renew=True,
            ),
            RenewCommand("glsgroupskip", ""),
            RenewCommand("arraystretch", "1.1"),
        ),
    )


def _GlsExtraKeys() -> TeX:
    return Block(
        *(
            GlsAddKey(
                key,
                "",
                entry=f"glsentry{stem}",
                entry_upper=f"Glsentry{stem}",
                cs=f"gls{stem}",
                cs_upper=f"Gls{stem}",
                cs_all=f"GLS{stem}",
            )
            for key, stem in (("genitive", "genitive"), ("dative", "dative"))
        )
    )


def _GlossaryStyleNative() -> TeX:
    return Block(
        _ColumnTypes(),
        _ManualFixedWidthStyle(),
        _GlsExtraKeys(),
    )


def GlossarySettingsBlock() -> TeX:
    return Block(
        Command("makeglossaries"),
        _GlossaryStyleNative(),
        SetGlossaryStyle("manualfixedwidth"),
        RenewCommand("entryname", "Wort/Abkürzung"),
        RenewCommand("descriptionname", "Bedeutung"),
        RenewCommand("pagelistname", "Seite(n)"),
        Command("glsenablehyper"),
        RenewCommand("glsclearpage", ""),
        RenewCommand("acronymname", "Abkürzungsverzeichnis"),
    )


__all__ = ["GlossarySettingsBlock"]
