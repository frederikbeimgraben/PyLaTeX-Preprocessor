"""The HSRT report document class and the nodes that build it."""

# The generic components moved to `pytex_components`. This package re-exports
# their modules and names, so `pytex_hsrtreport.ColoredBox` and
# `pytex_hsrtreport.boxes` still work.
from pytex_components import (
    ColoredBox,
    Conditionalpagebreak,
    Critical,
    CustomBox,
    DiscussionBox,
    DraftWatermark,
    Fcite,
    GermanCrefNames,
    ImportantBox,
    InfoBox,
    Keeptogether,
    Smartsection,
    Smartsubsection,
    SuccessBox,
    VotingResults,
    WarningBox,
    WatermarkCounter,
    WordcountCommands,
    boxes,
    citations,
    cleveref_names,
    pagebreak,
    voting,
    watermark,
    wordcount,
)

from . import (
    colors,
    document,
    fonts,
    glossary,
    hyperref_config,
    listings,
    logos,
    pagesetup,
    titlepage,
    variants,
)
from .colors import HSRT_PALETTE, HSRTColors
from .document import HSRTReport
from .fonts import HSRTFontSetup
from .glossary import AcrShortcut, HSRTGlossarySetup
from .hyperref_config import (
    HSRT_CITE_COLOR,
    HSRT_HYPER_OPTIONS,
    HSRT_LINK_COLOR,
    HSRT_URL_COLOR,
    HSRTHyperref,
)
from .listings import HSRTListingStyles, style_options
from .logos import DefaultLogos, Logo, LogoStrip, logo_path
from .pagesetup import HSRTPageSetup
from .titlepage import TitlePage, TitlePageDataLine
from .variants import Variant, default_logo_names

__all__ = [
    "HSRT_CITE_COLOR",
    "HSRT_HYPER_OPTIONS",
    "HSRT_LINK_COLOR",
    "HSRT_PALETTE",
    "HSRT_URL_COLOR",
    "AcrShortcut",
    "ColoredBox",
    "Conditionalpagebreak",
    "Critical",
    "CustomBox",
    "DefaultLogos",
    "DiscussionBox",
    "DraftWatermark",
    "Fcite",
    "GermanCrefNames",
    "HSRTColors",
    "HSRTFontSetup",
    "HSRTGlossarySetup",
    "HSRTHyperref",
    "HSRTListingStyles",
    "HSRTPageSetup",
    "HSRTReport",
    "ImportantBox",
    "InfoBox",
    "Keeptogether",
    "Logo",
    "LogoStrip",
    "Smartsection",
    "Smartsubsection",
    "SuccessBox",
    "TitlePage",
    "TitlePageDataLine",
    "Variant",
    "VotingResults",
    "WarningBox",
    "WatermarkCounter",
    "WordcountCommands",
    "boxes",
    "citations",
    "cleveref_names",
    "colors",
    "default_logo_names",
    "document",
    "fonts",
    "glossary",
    "hyperref_config",
    "listings",
    "logo_path",
    "logos",
    "pagebreak",
    "pagesetup",
    "style_options",
    "titlepage",
    "variants",
    "voting",
    "watermark",
    "wordcount",
]
