from dataclasses import dataclass, field
from typing import Final, override

from pytex.commands.fontspec import Setmainfont, Setsansfont
from pytex.commands.geometry import Geometry
from pytex.interface.package import PackageProtocol
from pytex.interface.tex import TeX
from pytex.model.concat import Concat
from pytex.model.empty import Empty
from pytex.model.raw import Raw
from pytex.packages import (
    BIBLATEX,
    CLEVEREF,
    CSQUOTES,
    ETOOLBOX,
    FONTAWESOME5,
    GEOMETRY,
    GLOSSARIES,
    GRAPHICX,
    HYPERREF,
    LISTINGS,
    LMODERN,
    MDFRAMED,
    PGF,
    PGFFOR,
    RAGGED2E,
    SCRLAYER_SCRPAGE,
    SETSPACE,
    TIKZ,
    XCOLOR,
)
from pytex.registry import Registry
from pytex_koma.document import KomaDocument

from .cleveref_names import GermanCrefNames
from .colors import HSRTColors
from .glossary import AcrShortcut, HSRTGlossarySetup
from .hyperref_config import HSRTHyperref
from .listings import HSRTListingStyles
from .logos import LogoSet
from .variants import Variant

_BASE_PACKAGES: Final[frozenset[PackageProtocol]] = frozenset(
    {
        LMODERN,
        GEOMETRY,
        GRAPHICX,
        XCOLOR,
        TIKZ,
        PGF,
        PGFFOR,
        LISTINGS,
        HYPERREF,
        CLEVEREF,
        BIBLATEX,
        CSQUOTES,
        GLOSSARIES,
        MDFRAMED,
        FONTAWESOME5,
        SCRLAYER_SCRPAGE,
        ETOOLBOX,
        SETSPACE,
        RAGGED2E,
    }
)

_DEFAULT_GEOMETRY: Final[dict[str, str]] = {
    "a4paper": "",
    "top": "2cm",
    "bottom": "2cm",
    "left": "2cm",
    "right": "2cm",
}


@Registry.add
@dataclass
class HSRTReport(KomaDocument):
    """Full HSRT report: scrbook-based KomaDocument + HSRT preamble + variant.

    All section/box/listing logic comes from sibling pytex_hsrtreport modules.
    """

    document_class: str = "scrbook"

    variant: Variant = Variant.METI
    show_toc: bool = True
    show_glossary: bool = False
    show_acronyms: bool = False
    show_bibliography: bool = False
    show_footer_logos: bool = False

    logos: LogoSet | None = None
    main_font: str | None = None
    sans_font: str | None = None
    geometry_options: dict[str, str] = field(default_factory=lambda: dict(_DEFAULT_GEOMETRY))
    user_preamble: TeX | str = Empty

    def __post_init__(self) -> None:
        super().__post_init__()
        # Force scrbook
        if self.document_class != "scrbook":
            raise ValueError(
                f"HSRTReport requires document_class='scrbook', got {self.document_class!r}"
            )
        self.extra_packages: frozenset[PackageProtocol] = (
            frozenset(self.extra_packages) | _BASE_PACKAGES
        )
        self.preamble: TeX | str = self._build_preamble()

    def _build_preamble(self) -> TeX:
        parts: list[TeX | str] = [
            Geometry(self.geometry_options),
            HSRTColors(),
            HSRTHyperref(),
            GermanCrefNames(),
            HSRTGlossarySetup() if (self.show_glossary or self.show_acronyms) else Empty,
            HSRTListingStyles(),
            AcrShortcut(),
        ]
        if self.main_font is not None:
            parts.append(Setmainfont(self.main_font))
        if self.sans_font is not None:
            parts.append(Setsansfont(self.sans_font))
        if self.logos is not None:
            parts.append(Raw(self.logos.rendered))
        if self.user_preamble is not Empty:
            parts.append(self.user_preamble)
        return Concat(*parts)

    @property
    @override
    def rendered(self) -> str:
        # Delegate to KomaDocument; extra_packages and preamble carry HSRT setup
        return super().rendered
