"""Glossary style + entry-name overrides."""

from pytex import (
    Command,
    IncludeTeX,
    NewCommand,
    RenewCommand,
    TeX,
)
from pytex_komascript.model import Block

from ..paths import TEX_DIR


def glossary_settings_block() -> TeX:
    return Block(
        Command("makeglossaries"),
        IncludeTeX(TEX_DIR / "glossary_style.tex"),
        Command("setglossarystyle", "manualfixedwidth"),
        RenewCommand("entryname", "Wort/Abkürzung"),
        RenewCommand("descriptionname", "Bedeutung"),
        RenewCommand("pagelistname", "Seite(n)"),
        Command("glsenablehyper"),
        RenewCommand("glsclearpage", ""),
        RenewCommand("acronymname", "Abkürzungsverzeichnis"),
        NewCommand("acr", "\\acrshort"),
    )


__all__ = ["glossary_settings_block"]
