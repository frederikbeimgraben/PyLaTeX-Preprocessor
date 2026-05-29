"""HSRT report layout built on :mod:`pytex` and :mod:`pytex_komascript`.

Reproduces the original ``HSRTReport`` LaTeX document class as a Python builder:
:func:`HSRTReport` emits a ``scrbook`` document with the full HSRT preamble, with
all class logic (variant logos, glossary/bibliography toggles, word count)
computed in Python rather than in TeX.

Example:
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
    Glossary,
    GlossaryEntry,
    Listing,
    MakeGlossaries,
    PrintGlossary,
    acr,
    acrfull,
    acrlong,
    gls,
    glspl,
)

from .colors import COLOR_DEFS, DefineColor
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
from .variants import VARIANT_LOGOS, Logo, Variant, resolve_logos
from .wordcount import content_text, count_words

# Re-export the most commonly used native pytex preamble primitives so
# downstream documents can build extra blocks without reaching into
# ``pytex.library.builtins`` directly.
from pytex import (
    AtBeginDocument,
    AtEndDocument,
    BuiltinPackages,
    Crefname,
    Hypersetup,
    NewCommand,
    NewEnvironment,
    Package,
    RenewCommand,
    SetLength,
)

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
    "DefineColor",
    "COLOR_DEFS",
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
