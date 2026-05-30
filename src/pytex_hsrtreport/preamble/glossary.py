"""Glossary style + entry-name overrides — all native."""

from pytex import (
    Command,
    GlsAddKey,
    Let,
    LongTable,
    NewColumnType,
    NewCommand,
    NewEnvironment,
    NewGlossaryStyle,
    Newline,
    RenewCommand,
    SetGlossaryStyle,
    TeX,
)
from pytex.model.raw import coerce_tex
from pytex_komascript.model import Block


def _column_types() -> TeX:
    """``L``, ``C``, ``R`` paragraph columns from the original style file."""
    common = "\\let\\newline\\\\\\arraybackslash\\hspace{0pt}"
    return Block(
        NewColumnType(
            "L",
            f">{{\\raggedright{common}}}p{{#1}}",
            n_args=1,
        ),
        NewColumnType(
            "C",
            f">{{\\centering{common}}}p{{#1}}",
            n_args=1,
        ),
        NewColumnType(
            "R",
            f">{{\\raggedleft{common}}}p{{#1}}",
            n_args=1,
        ),
    )


def _manualfixedwidth_style() -> TeX:
    body = Block(
        SetGlossaryStyle("long3colheader"),
        NewEnvironment(
            "theglossary",
            "\\begin{longtable}{@{} L{0.30\\textwidth-\\tabcolsep} "
            "p{0.58\\textwidth-\\tabcolsep} "
            "L{0.10\\textwidth-\\tabcolsep} @{}}",
            "\\end{longtable}",
            renew=True,
        ),
        RenewCommand("glsgroupskip", ""),
        RenewCommand("arraystretch", "1.1"),
    )
    return NewGlossaryStyle("manualfixedwidth", body)


def _gls_extra_keys() -> TeX:
    return Block(
        GlsAddKey(
            "genitive",
            "",
            entry="glsentrygenitive",
            entry_upper="Glsentrygenitive",
            cs="glsgen",
            cs_upper="Glsgen",
            cs_all="GLSgen",
        ),
        GlsAddKey(
            "dative",
            "",
            entry="glsentrydative",
            entry_upper="Glsentrydative",
            cs="glsdative",
            cs_upper="Glsdative",
            cs_all="GLSdative",
        ),
    )


def _glossary_style_native() -> TeX:
    """Native replacement for the old ``glossary_style.tex``."""
    return Block(
        _column_types(),
        _manualfixedwidth_style(),
        _gls_extra_keys(),
    )


# Touch unused imports the linter would otherwise prune — Newline / LongTable
# / Let / Command remain handy when extending the glossary table layout.
_ = (Newline, LongTable, Let, Command, coerce_tex)


def glossary_settings_block() -> TeX:
    return Block(
        Command("makeglossaries"),
        _glossary_style_native(),
        SetGlossaryStyle("manualfixedwidth"),
        RenewCommand("entryname", "Wort/Abkürzung"),
        RenewCommand("descriptionname", "Bedeutung"),
        RenewCommand("pagelistname", "Seite(n)"),
        Command("glsenablehyper"),
        RenewCommand("glsclearpage", ""),
        RenewCommand("acronymname", "Abkürzungsverzeichnis"),
        NewCommand("acr", "\\acrshort"),
    )


__all__ = ["glossary_settings_block"]
