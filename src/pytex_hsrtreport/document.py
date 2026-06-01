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
from pytex.model.document_class import DocumentClass
from pytex.model.empty import Empty
from pytex.model.environment import Environment
from pytex.model.raw import Raw
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
from .fonts import HSRTFontSetup
from .glossary import AcrShortcut, HSRTGlossarySetup
from .hyperref_config import (
    HSRT_CITE_COLOR,
    HSRT_LINK_COLOR,
    HSRT_URL_COLOR,
    HSRTHyperref,
)
from .listings import HSRTListingStyles
from .logos import DefaultLogos, footer_logo_hook
from .pagesetup import HSRTPageSetup
from .titlepage import TitlePage, TitlePageDataLine
from .variants import Variant, default_logo_names

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
    show_titlepage: bool = True
    show_glossary: bool = False
    show_acronyms: bool = False
    show_bibliography: bool = False
    show_footer_logos: bool = False

    title: TeX | str | None = None
    author: TeX | str | None = None
    abstract: TeX | str | None = None
    keywords: TeX | str | None = None
    data_lines: tuple[TitlePageDataLine, ...] = ()

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
            Raw(r"\KOMAoptions{open=any,twoside=false}"),
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
        # Page setup first — provides \providecommand{\blenderfont} fallback
        # that HSRTFontSetup's \renewcommand{\blenderfont} requires.
        parts.append(HSRTPageSetup())
        if self.show_footer_logos:
            parts.append(
                Raw(
                    footer_logo_hook(default_logo_names(self.variant)),
                    allow_replacements=False,
                )
            )
        else:  # skyline on every page even without footer logos
            parts.append(
                Raw(
                    footer_logo_hook((), skyline=True),
                    allow_replacements=False,
                )
            )
        if self.inline_fonts:
            parts.append(HSRTFontSetup())
        if self.main_font is not None:
            parts.append(Setmainfont(self.main_font))
        if self.sans_font is not None:
            parts.append(Setsansfont(self.sans_font))
        # \title / \author for running headers
        if self.title is not None:
            parts.append(Raw(f"\\title{{{coerce_tex(self.title).rendered}}}"))
        if self.author is not None:
            parts.append(Raw(f"\\author{{{coerce_tex(self.author).rendered}}}"))
        if self.user_preamble is not Empty:
            parts.append(self.user_preamble)
        return Concat(*parts)

    def _build_full_body(self) -> TeX:
        """Wrap user body with front/main/back matter, ToC, glossary, bibliography."""
        parts: list[TeX | str] = []

        # -- Front matter --
        parts.append(Raw(r"\frontmatter"))

        # Title page
        if self.show_titlepage and self.title is not None:
            parts.append(
                TitlePage(
                    title=self.title,
                    abstract=self.abstract or "",
                    keywords=self.keywords or "",
                    data_lines=self.data_lines,
                    logo_names=default_logo_names(self.variant),
                )
            )

        # Table of contents
        if self.show_toc:
            parts.append(Raw(r"\newpage\tableofcontents"))

        # -- Main matter --
        parts.append(Raw(r"\mainmatter"))
        parts.append(coerce_tex(self.body))

        # Back matter header is only emitted when there is actual back-matter content.
        # \backmatter calls hyperref's \bookmarksetup which fires \@ in vertical mode
        # and crashes — skip it entirely when there is nothing to show.
        if self.show_glossary or self.show_acronyms or self.show_bibliography:
            parts.append(Raw(r"\newpage\appendix\backmatter\HSRTBackMattertrue"))

        if self.show_glossary:
            parts.append(
                Raw(
                    r"\renewcommand*{\entryname}{Wort}\clearpage\vspace*{-2.25em}\printglossary"
                )
            )
        if self.show_acronyms:
            parts.append(
                Raw(
                    r"\renewcommand*{\entryname}{Abkürzung}\clearpage\vspace*{-2.25em}\printglossary[type=\acronymtype,title=Abkürzungen]"
                )
            )
        if self.show_bibliography:
            parts.append(
                Raw(
                    r"\clearpage\chapter*{Literaturverzeichnis}\label{chap:bibliography}\printbibliography[heading=none,title={}]"
                )
            )

        return Concat(*parts)

    def write_inline_fonts(self, target_dir: str = ".") -> tuple[str, ...]:
        """Write bundled font TTF files to ``<target_dir>/fonts/`` for compilation.

        Call this before the TeX run so fontspec can resolve the font paths
        embedded in the preamble by `HSRTFontSetup`.
        """
        if not self.inline_fonts:
            return ()
        from .fonts import FONT_OUTPUT_DIR, all_font_paths, rel

        base = Path(target_dir)
        written: list[str] = []
        for font_path in all_font_paths():
            dest = base / FONT_OUTPUT_DIR / rel(font_path)
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_bytes(font_path.read_bytes())
            written.append(dest.as_posix())
        return tuple(written)

    def write_inline_logos(self, target_dir: str = ".") -> tuple[str, ...]:
        """Write the logos used by the tikz overlays to ``<target_dir>/logos/``.

        The titlepage overlay and footer hook reference logos by relative path
        (``logos/<file>``); this materialises those files next to the .tex so
        tectonic can read them without tripping its absolute-path restrictions.
        SVG sources are converted to PDF via `IncludeImage`.
        """
        from pytex.model.image import IncludeImage

        from .logos import LOGO_OUTPUT_DIR, logo_output_name, logo_path

        # Titlepage overlay + footer hook use the variant defaults; the footer
        # skyline is emitted on every page regardless of show_footer_logos.
        names = set(default_logo_names(self.variant)) | {"Skyline"}
        base = Path(target_dir)
        written: list[str] = []
        for name in sorted(names):
            img = IncludeImage(path=logo_path(name), inline_base64=False)
            dest = base / LOGO_OUTPUT_DIR / logo_output_name(name)
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_bytes(img.read_bytes())  # converts svg -> pdf
            written.append(dest.as_posix())
        return tuple(written)

    def default_logos(self) -> TeX:
        return DefaultLogos(self.variant, inline_base64=self.inline_logos)

    @property
    @override
    def rendered(self) -> str:
        return Concat(
            DocumentClass(self.document_class, self.document_class_options),
            *self.ordered_packages(),
            self.inline_image_block,
            self.preamble,
            Environment("document", self._build_full_body()),
        ).rendered
