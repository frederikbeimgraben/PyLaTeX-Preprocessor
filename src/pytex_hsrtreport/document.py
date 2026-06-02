from collections.abc import Iterator
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
    ARRAY,
    BABEL,
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
    LONGTABLE,
    MDFRAMED,
    NEEDSPACE,
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

__all__ = ["HSRTReport"]

BASE_PACKAGES: Final[frozenset[PackageProtocol]] = frozenset(
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
        ARRAY,
        LONGTABLE,
        NEEDSPACE,
        BABEL,
    }
)

DEFAULT_GEOMETRY: Final[dict[str, str]] = {
    "a4paper": "",
    "top": "2cm",
    "bottom": "2cm",
    "left": "2cm",
    "right": "2cm",
}

# Back-matter print commands. \printglossary/\printbibliography emit their own
# \chapter* heading (and page break), so no manual \clearpage precedes them.
BACKMATTER_HEADER = r"\newpage\appendix\backmatter\HSRTBackMattertrue"
GLOSSARY_PRINT = r"\renewcommand*{\entryname}{Wort}\printglossary"
ACRONYM_PRINT = r"\renewcommand*{\entryname}{Abkürzung}\printglossary[type=\acronymtype,title=Abkürzungen]"  # noqa: E501
BIBLIOGRAPHY_PRINT = r"\clearpage\chapter*{Literaturverzeichnis}\label{chap:bibliography}\printbibliography[heading=none,title={}]"  # noqa: E501


def _emit(dest: Path, data: bytes) -> str:
    """Write `data` to `dest` (creating parent dirs) and return its posix path."""
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_bytes(data)
    return dest.as_posix()


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
        default_factory=lambda: dict(DEFAULT_GEOMETRY)
    )
    user_preamble: TeX | str = Empty

    def __post_init__(self) -> None:
        super().__post_init__()
        if self.document_class != "scrbook":
            raise ValueError(
                "HSRTReport requires document_class='scrbook', "
                + f"got {self.document_class!r}"
            )
        self.extra_packages: frozenset[PackageProtocol] = (
            frozenset(self.extra_packages) | BASE_PACKAGES
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
        return Concat(*self._preamble_parts())

    def _preamble_parts(self) -> Iterator[TeX | str]:
        yield Raw(r"\KOMAoptions{open=any,twoside=false}")
        yield Geometry(self.geometry_options)
        yield HSRTColors()
        yield self._color_definitions()
        yield HSRTHyperref()
        yield GermanCrefNames()
        if self.show_glossary or self.show_acronyms:
            yield HSRTGlossarySetup()
        yield HSRTListingStyles()
        yield AcrShortcut()
        # Page setup first — provides \providecommand{\blenderfont} fallback
        # that HSRTFontSetup's \renewcommand{\blenderfont} requires.
        yield HSRTPageSetup()
        # The skyline is drawn on every page; footer logos only when requested.
        logo_names = default_logo_names(self.variant) if self.show_footer_logos else ()
        yield Raw(footer_logo_hook(logo_names), allow_replacements=False)
        if self.inline_fonts:
            yield HSRTFontSetup()
        if self.main_font is not None:
            yield Setmainfont(self.main_font)
        if self.sans_font is not None:
            yield Setsansfont(self.sans_font)
        # \title / \author for running headers
        if self.title is not None:
            yield Raw(f"\\title{{{coerce_tex(self.title).rendered}}}")
        if self.author is not None:
            yield Raw(f"\\author{{{coerce_tex(self.author).rendered}}}")
        if self.user_preamble is not Empty:
            yield self.user_preamble

    def _build_full_body(self) -> TeX:
        """Wrap user body with front/main/back matter, ToC, glossary, bibliography."""
        return Concat(*self._body_parts())

    def _body_parts(self) -> Iterator[TeX | str]:
        # -- Front matter --
        # Trailing newlines keep these matter macros from running into whatever
        # follows: a body that starts with plain text would otherwise produce
        # e.g. `\mainmatterThis ...` (an undefined control sequence).
        yield Raw("\\frontmatter\n")
        if self.show_titlepage and self.title is not None:
            yield TitlePage(
                title=self.title,
                abstract=self.abstract or "",
                keywords=self.keywords or "",
                data_lines=self.data_lines,
                logo_names=default_logo_names(self.variant),
            )
        if self.show_toc:
            yield Raw(r"\newpage\tableofcontents")

        # -- Main matter --
        yield Raw("\\mainmatter\n")
        yield coerce_tex(self.body)

        # -- Back matter --
        # The header is only emitted when there is actual back-matter content:
        # \backmatter calls hyperref's \bookmarksetup which fires \@ in vertical
        # mode and crashes, so skip it entirely when there is nothing to show.
        if self.show_glossary or self.show_acronyms or self.show_bibliography:
            yield Raw(BACKMATTER_HEADER)
        if self.show_glossary:
            yield Raw(GLOSSARY_PRINT)
        if self.show_acronyms:
            yield Raw(ACRONYM_PRINT)
        if self.show_bibliography:
            yield Raw(BIBLIOGRAPHY_PRINT)

    def write_inline_fonts(self, target_dir: str = ".") -> tuple[str, ...]:
        """Write bundled font TTF files to ``<target_dir>/fonts/`` for compilation.

        Call this before the TeX run so fontspec can resolve the font paths
        embedded in the preamble by `HSRTFontSetup`.
        """
        if not self.inline_fonts:
            return ()
        from .fonts import FONT_OUTPUT_DIR, all_font_paths, rel

        base = Path(target_dir)
        return tuple(
            _emit(base / FONT_OUTPUT_DIR / rel(font_path), font_path.read_bytes())
            for font_path in all_font_paths()
        )

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
        names = sorted(set(default_logo_names(self.variant)) | {"Skyline"})
        base = Path(target_dir)
        return tuple(
            # IncludeImage.read_bytes converts svg -> pdf on the fly.
            _emit(
                base / LOGO_OUTPUT_DIR / logo_output_name(name),
                IncludeImage(path=logo_path(name), inline_base64=False).read_bytes(),
            )
            for name in names
        )

    def default_logos(self) -> TeX:
        return DefaultLogos(self.variant, inline_base64=self.inline_logos)

    @property
    @override
    def rendered(self) -> str:
        return Concat(
            DocumentClass(self.document_class, self.document_class_options),
            # hyperfootnotes is only honoured as a hyperref load option, so it
            # must be queued before \usepackage{hyperref}. The HSRT footnote
            # setup never places hyperref's Hfootnote destination, so leaving
            # footnote-mark links enabled produces dangling links.
            Raw(r"\PassOptionsToPackage{hyperfootnotes=false}{hyperref}"),
            *self.ordered_packages(),
            self.inline_image_block,
            self.preamble,
            Environment("document", self._build_full_body()),
        ).rendered
