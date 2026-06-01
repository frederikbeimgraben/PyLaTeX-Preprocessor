from dataclasses import dataclass, field
from pathlib import Path
from typing import Final, override

from pytex.commands.colors import Definecolor
from pytex.commands.fontspec import Setmainfont, Setsansfont
from pytex.commands.geometry import Geometry
from pytex.helpers.coerce import coerce_tex
from pytex.interface.package import PackageProtocol
from pytex.interface.tex import TeX
from pytex.model.color import Color, collect_colors
from pytex.model.concat import Concat
from pytex.model.empty import Empty
from pytex.packages import (
    BIBLATEX,
    CLEVEREF,
    CSQUOTES,
    ETOOLBOX,
    FONTAWESOME,
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
from .fonts import HSRTFontSetup, HSRTInlineFonts
from .glossary import AcrShortcut, HSRTGlossarySetup
from .hyperref_config import (
    HSRT_CITE_COLOR,
    HSRT_LINK_COLOR,
    HSRT_URL_COLOR,
    HSRTHyperref,
)
from .listings import HSRTListingStyles
from .logos import DefaultLogos
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
        FONTAWESOME,
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
    """HSRT report: scrbook + KomaDocument + auto preamble + colour-collector."""

    document_class: str = "scrbook"

    variant: Variant = Variant.INF
    show_toc: bool = True
    show_glossary: bool = False
    show_acronyms: bool = False
    show_bibliography: bool = False
    show_footer_logos: bool = False

    inline_logos: bool = True
    inline_fonts: bool = True
    main_font: str | None = None
    sans_font: str | None = None
    geometry_options: dict[str, str] = field(
        default_factory=lambda: dict(_DEFAULT_GEOMETRY)
    )
    user_preamble: TeX | str = Empty

    def __post_init__(self) -> None:
        super().__post_init__()
        if self.document_class != "scrbook":
            raise ValueError(
                f"HSRTReport requires document_class='scrbook', got {self.document_class!r}"
            )
        self.extra_packages: frozenset[PackageProtocol] = (
            frozenset(self.extra_packages) | _BASE_PACKAGES
        )
        self.preamble: TeX | str = self._build_preamble()

    def discovered_colors(self) -> tuple[Color, ...]:
        """Walk body + preamble, return every `Color` instance needing `\\definecolor`.

        Also includes HSRT hyperref colours (stored as Python data inside the
        hypersetup options dict, so unreachable via the tree walk).
        """
        seen: dict[str, Color] = {}
        for c in (HSRT_CITE_COLOR, HSRT_LINK_COLOR, HSRT_URL_COLOR):
            seen.setdefault(c.name, c)
        for root in (self.body, self.user_preamble):
            for color in collect_colors(coerce_tex(root)):
                seen.setdefault(color.name, color)
        return tuple(seen.values())

    def _color_definitions(self) -> TeX:
        return Concat(
            *(
                Definecolor(c.name, c.spec.model, c.spec.value)
                for c in self.discovered_colors()
                if c.spec is not None
            )
        )

    def _build_preamble(self) -> TeX:
        parts: list[TeX | str] = [
            Geometry(self.geometry_options),
            HSRTColors(),
            self._color_definitions(),
            HSRTHyperref(),
            GermanCrefNames(),
            HSRTGlossarySetup()
            if (self.show_glossary or self.show_acronyms)
            else Empty,
            HSRTListingStyles(),
            AcrShortcut(),
        ]
        if self.inline_fonts:
            parts.append(HSRTFontSetup())
        if self.main_font is not None:
            parts.append(Setmainfont(self.main_font))
        if self.sans_font is not None:
            parts.append(Setsansfont(self.sans_font))
        if self.user_preamble is not Empty:
            parts.append(self.user_preamble)
        return Concat(*parts)

    def write_inline_fonts(self, target_dir: str = ".") -> tuple[str, ...]:
        """Write bundled font TTF files to ``<target_dir>/fonts/`` for compilation.

        Call this before the TeX run so fontspec can resolve the font paths
        embedded in the preamble by `HSRTFontSetup`.
        """
        if not self.inline_fonts:
            return ()
        from .fonts import (
            FONT_OUTPUT_DIR,
            all_font_paths,
            rel,
        )

        base = Path(target_dir)
        written: list[str] = []
        for font_path in all_font_paths():
            dest = base / FONT_OUTPUT_DIR / rel(font_path)
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_bytes(font_path.read_bytes())
            written.append(dest.as_posix())
        return tuple(written)

    def default_logos(self) -> TeX:
        return DefaultLogos(self.variant, inline_base64=self.inline_logos)

    @property
    def inline_font_block(self) -> TeX:
        """filecontents* base64 blocks for all bundled fonts, or Empty."""
        if not self.inline_fonts:
            return Empty
        return HSRTInlineFonts()

    @property
    @override
    def inline_image_block(self) -> TeX:
        """Prepend font blocks to the image blocks emitted by the base class."""
        base = super().inline_image_block
        font_block = self.inline_font_block
        if font_block is Empty:
            return base
        if base is Empty:
            return font_block
        return Concat(font_block, base)

    @property
    @override
    def rendered(self) -> str:
        return super().rendered
