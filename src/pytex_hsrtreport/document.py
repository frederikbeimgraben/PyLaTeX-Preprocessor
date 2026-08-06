"""The `HSRTReport` document class, its preamble and its inline assets."""

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
from pytex_components.cleveref_names import GermanCrefNames
from pytex_koma.document import KomaDocument

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
from .variants import Variant, default_logo_names, footer_logo_names

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

# The back-matter print commands. `\printglossary` writes its own `\chapter*`
# heading and page break, so no manual `\clearpage` comes before it.
# `\printbibliography` runs with `heading=none`, so the command string below
# carries its own `\clearpage` and `\chapter*` heading.
BACKMATTER_HEADER = r"\newpage\appendix\backmatter\HSRTBackMattertrue"
GLOSSARY_PRINT = r"\renewcommand*{\entryname}{Wort}\printglossary"
ACRONYM_PRINT = r"\renewcommand*{\entryname}{Abkürzung}\printglossary[type=\acronymtype,title=Abkürzungen]"  # noqa: E501
BIBLIOGRAPHY_PRINT = r"\clearpage\chapter*{Literaturverzeichnis}\label{chap:bibliography}\printbibliography[heading=none,title={}]"  # noqa: E501


def _emit(dest: Path, data: bytes) -> str:
    """Write `data` to `dest` and return the posix path of `dest`.

    The function creates the parent directories when they do not exist.
    """
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_bytes(data)
    return dest.as_posix()


@Registry.add
@dataclass
class HSRTReport(KomaDocument):
    """An HSRT report that uses the `scrbook` document class.

    The class extends `KomaDocument`. It builds its own preamble and collects
    the colors that the body and `user_preamble` use.
    """

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
    abstract_heading: str = "Abstract"
    keywords_heading: str = "Keywords"
    # Title-page logos, given as vendored names or as custom file paths.
    # `None` selects the default set of the variant.
    logos: tuple[str, ...] | None = None
    # Footer logos, with the same value form as `logos`. `None` selects the
    # footer set of the variant.
    footer_logos: tuple[str, ...] | None = None
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
        r"""Return every `Color` that needs a `\definecolor` command.

        The walk covers the body, `user_preamble` and the title-page fields
        `title`, `abstract`, `keywords` and `data_lines`. The result also
        holds the three HSRT hyperref colors. Those live as Python data
        inside the hypersetup options dictionary, so the walk cannot reach
        them.
        """
        seen: dict[str, Color] = {}
        for c in (HSRT_CITE_COLOR, HSRT_LINK_COLOR, HSRT_URL_COLOR):
            seen.setdefault(c.name, c)
        roots: tuple[TeX | str, ...] = (
            self.body,
            self.user_preamble,
            self.title or "",
            self.abstract or "",
            self.keywords or "",
            *(line.value for line in self.data_lines),
        )
        for root in roots:
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
        # The page setup comes first. It provides the
        # `\providecommand{\blenderfont}` fallback that the
        # `\renewcommand{\blenderfont}` in `HSRTFontSetup` needs.
        yield HSRTPageSetup()
        # LaTeX draws the skyline on every page. The footer logos appear only
        # when `show_footer_logos` is true.
        logo_names = self._footer_logos() if self.show_footer_logos else ()
        yield Raw(footer_logo_hook(logo_names), allow_replacements=False)
        if self.inline_fonts:
            yield HSRTFontSetup()
        if self.main_font is not None:
            yield Setmainfont(self.main_font)
        if self.sans_font is not None:
            yield Setsansfont(self.sans_font)
        # `\title` and `\author` feed the running headers.
        if self.title is not None:
            yield Raw(f"\\title{{{coerce_tex(self.title).rendered}}}")
        if self.author is not None:
            yield Raw(f"\\author{{{coerce_tex(self.author).rendered}}}")
        if self.user_preamble is not Empty:
            yield self.user_preamble

    def _build_full_body(self) -> TeX:
        """Wrap the body with the front matter, main matter and back matter.

        The wrapper adds the title page, the table of contents, the glossary,
        the acronym list and the bibliography when the matching flag is set.
        """
        return Concat(*self._body_parts())

    def _body_parts(self) -> Iterator[TeX | str]:
        # The trailing newline keeps a matter macro apart from the text that
        # follows it. Without the newline, a body that starts with plain text
        # gives `\mainmatterThis ...`, an undefined control sequence.
        yield Raw("\\frontmatter\n")
        if self.show_titlepage and self.title is not None:
            yield TitlePage(
                title=self.title,
                abstract=self.abstract or "",
                keywords=self.keywords or "",
                data_lines=self.data_lines,
                logo_names=self._title_logos(),
                abstract_heading=self.abstract_heading,
                keywords_heading=self.keywords_heading,
            )
        if self.show_toc:
            yield Raw(r"\newpage\tableofcontents")

        yield Raw("\\mainmatter\n")
        yield coerce_tex(self.body)

        # Write the header only when the back matter has content.
        # `\backmatter` calls the hyperref macro `\bookmarksetup`, which runs
        # `\@` in vertical mode and crashes. Skip the header when there is
        # nothing to show.
        if self.show_glossary or self.show_acronyms or self.show_bibliography:
            yield Raw(BACKMATTER_HEADER)
        if self.show_glossary:
            yield Raw(GLOSSARY_PRINT)
        if self.show_acronyms:
            yield Raw(ACRONYM_PRINT)
        if self.show_bibliography:
            yield Raw(BIBLIOGRAPHY_PRINT)

    def write_inline_fonts(self, target_dir: str = ".") -> tuple[str, ...]:
        """Write the bundled TTF font files to `<target_dir>/fonts/`.

        Call this method before you compile the document. fontspec then finds
        the font paths that `HSRTFontSetup` put in the preamble.

        Args:
            target_dir: The directory that holds the rendered `.tex` file.

        Returns:
            The posix path of each font file written. An empty tuple when
            `inline_fonts` is false.
        """
        if not self.inline_fonts:
            return ()
        from .fonts import FONT_OUTPUT_DIR, all_font_paths, rel

        base = Path(target_dir)
        return tuple(
            _emit(base / FONT_OUTPUT_DIR / rel(font_path), font_path.read_bytes())
            for font_path in all_font_paths()
        )

    def _title_logos(self) -> tuple[str, ...]:
        """Return the explicit `logos` value, or the default set of the variant."""
        if self.logos is not None:
            return self.logos
        return default_logo_names(self.variant)

    def _footer_logos(self) -> tuple[str, ...]:
        """Return the explicit `footer_logos` value, or the footer set of the variant.

        Returns:
            The footer logo names. The variant supplies them when
            `footer_logos` is `None`.
        """
        if self.footer_logos is not None:
            return self.footer_logos
        return footer_logo_names(self.variant)

    def write_inline_logos(self, target_dir: str = ".") -> tuple[str, ...]:
        """Write the logos of the tikz overlays to `<target_dir>/logos/`.

        The title page overlay and the footer hook name each logo by a path
        relative to the rendered `.tex` file (`logos/<file>`). This method
        writes the files to disk next to that `.tex` file. The tectonic binary
        then reads them. Its restrictions on absolute paths do not apply.
        `IncludeImage` converts an SVG source to PDF.

        Args:
            target_dir: The directory that holds the rendered `.tex` file.

        Returns:
            The posix path of each logo file written.
        """
        from pytex.model.image import IncludeImage

        from .logos import LOGO_OUTPUT_DIR, logo_output_name, logo_path

        # The title page overlay uses the title logos. The footer hook uses
        # its own set, which can differ. MAKERS is one such variant. LaTeX
        # draws the skyline on every page, whatever `show_footer_logos` is.
        names = sorted(
            set(self._title_logos()) | set(self._footer_logos()) | {"Skyline"}
        )
        base = Path(target_dir)
        return tuple(
            _emit(
                base / LOGO_OUTPUT_DIR / logo_output_name(name),
                IncludeImage(path=logo_path(name), inline_base64=False).read_bytes(),
            )
            for name in names
        )

    def default_logos(self) -> TeX:
        """Return the default logos of the variant as a horizontal row."""
        return DefaultLogos(self.variant, inline_base64=self.inline_logos)

    @property
    @override
    def rendered(self) -> str:
        return Concat(
            DocumentClass(self.document_class, self.document_class_options),
            # hyperref accepts `hyperfootnotes` only as a load option, so this
            # line must come before `\usepackage{hyperref}`. The HSRT footnote
            # setup never places the hyperref `Hfootnote` destination, so
            # links on the footnote marks would dangle.
            Raw(r"\PassOptionsToPackage{hyperfootnotes=false}{hyperref}"),
            *self.ordered_packages(),
            self.inline_image_block,
            self.preamble,
            Environment("document", self._build_full_body()),
        ).rendered
