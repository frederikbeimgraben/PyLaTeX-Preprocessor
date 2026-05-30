"""HSRT report layout built on :mod:`pytex`, :mod:`pytex_komascript`, and
:mod:`pytex_tikz`.

:func:`HSRTReport` emits a ``scrbook`` document with the full HSRT preamble;
every per-document branching decision (variant logos, glossary/bibliography
toggles, watermark text, scale factors, font availability, ...) is computed in
Python rather than encoded in TeX macros.

Example::

    from pytex import Group, Raw, Section
    from pytex_hsrtreport import HSRTReport, InfoBox

    doc = HSRTReport(
        content=Group(Section(Raw("Intro")), InfoBox(Raw("Hello"))),
        title="My Report",
        author="Jane Doe",
        variant="INF_meti",
        toc=True,
        wordcount=True,
    )
    print(doc.serialize())
"""

# Re-export the general glossary/listing primitives for convenience.
from pytex import (
    Acronyms,
    AcronymEntry,
    AtBeginDocument,
    AtEndDocument,
    BuiltinPackages,
    Crefname,
    Glossary,
    GlossaryEntry,
    Hypersetup,
    Listing,
    MakeGlossaries,
    NewCommand,
    NewEnvironment,
    Package,
    PrintGlossary,
    RenewCommand,
    SetLength,
    acr,
    acrfull,
    acrlong,
    gls,
    glspl,
)

from .colors import (
    COLOR_DEFS,
    Color,
    ColorBritishRacingGreen,
    ColorEggplant,
    ColorHanblue,
    ColorNavyblue,
    ColorPansypurple,
    ColorShockingpink,
    DefineColor,
    HSRTColor,
)
from .document import HSRTReport
from .infoblocks import (
    ColoredBox,
    CustomBox,
    DiscussionBox,
    ImportantBox,
    InfoBox,
    SuccessBox,
    VotingResults,
    WarningBox,
)
from .markdown import Markdown, markdown_to_tex
from .paths import (
    ASSETS_DIR,
    AssetPath,
    ClassPath,
    DummyFootPath,
    FontsPath,
    ImagesPath,
    LogosPath,
    SkylinePath,
    TEX_DIR,
    logo_pdf,
)
from .variants import VARIANT_LOGOS, Logo, Variant, resolve_logos
from .wordcount import content_text, count_words

__version__ = "0.1.0"

__all__ = [
    "__version__",
    "HSRTReport",
    # Variants & logos
    "Variant",
    "Logo",
    "VARIANT_LOGOS",
    "resolve_logos",
    # Info blocks
    "ColoredBox",
    "InfoBox",
    "WarningBox",
    "SuccessBox",
    "ImportantBox",
    "DiscussionBox",
    "CustomBox",
    "VotingResults",
    # Colors
    "HSRTColor",
    "DefineColor",
    "COLOR_DEFS",
    "Color",
    "ColorBritishRacingGreen",
    "ColorEggplant",
    "ColorHanblue",
    "ColorNavyblue",
    "ColorPansypurple",
    "ColorShockingpink",
    # Asset paths
    "ASSETS_DIR",
    "TEX_DIR",
    "AssetPath",
    "ClassPath",
    "FontsPath",
    "ImagesPath",
    "LogosPath",
    "SkylinePath",
    "DummyFootPath",
    "logo_pdf",
    # Glossary primitives (from pytex)
    "Glossary",
    "GlossaryEntry",
    "Acronyms",
    "AcronymEntry",
    "MakeGlossaries",
    "PrintGlossary",
    "gls",
    "glspl",
    "acr",
    "acrlong",
    "acrfull",
    # Listings
    "Listing",
    # Word count
    "count_words",
    "content_text",
    # Markdown
    "Markdown",
    "markdown_to_tex",
    # Native pytex primitives (re-exported)
    "AtBeginDocument",
    "AtEndDocument",
    "BuiltinPackages",
    "Crefname",
    "Hypersetup",
    "NewCommand",
    "NewEnvironment",
    "Package",
    "RenewCommand",
    "SetLength",
]
