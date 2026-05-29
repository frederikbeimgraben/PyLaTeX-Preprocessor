"""KOMA-Script document built on top of :class:`pytex.Document`."""

from collections.abc import Mapping
from datetime import datetime
from typing import Literal, override

from pytex import Document, Package, TeX
from pytex.model.raw import coerce_tex

from .commands import (
    SCRLAYER_SCRPAGE,
    ArgCommand,
    CFoot,
    CHead,
    ClearPairOfPageStyles,
    Dedication,
    Extratitle,
    IFoot,
    IHead,
    OFoot,
    OHead,
    Pagestyle,
    Publishers,
    SetKomaFont,
    Subject,
    TitleHead,
)
from .model import Block

#: KOMA-Script document classes.
type KomaClass = Literal["scrartcl", "scrreprt", "scrbook", "scrlttr2"]

#: Values accepted by the KOMA ``parskip`` option.
type ParSkip = Literal[
    "false",
    "full",
    "full-",
    "full+",
    "full*",
    "half",
    "half-",
    "half+",
    "half*",
    "never",
]

#: ``DIV`` factor: an explicit number of columns or a KOMA keyword.
type DivValue = int | Literal["calc", "classic", "current", "default", "last"]


class KomaDocument(TeX):
    """A KOMA-Script document (``scrartcl`` / ``scrreprt`` / ``scrbook``).

    Wraps :class:`pytex.Document`, translating KOMA-specific settings into
    ``\\documentclass`` options and preamble commands. Header/footer fields use
    the ``scrlayer-scrpage`` interface, which is added to the package list
    automatically whenever any header/footer or separator line is configured.

    Args:
        content: Main document body.
        document_class: KOMA class name (default ``"scrartcl"``).
        title / author / date / toc: Standard document metadata (see
            :class:`pytex.Document`).
        packages: Extra packages to load.
        preamble: Additional preamble content, emitted after the KOMA setup.

        font_size: Base font size, e.g. ``"11pt"`` (``fontsize=`` option).
        paper_size: Paper size token, e.g. ``"a4paper"``.
        div: Type-area ``DIV`` factor (int or ``"calc"``/``"classic"``).
        bcor: Binding correction ``BCOR``, e.g. ``"10mm"``.
        parskip: Paragraph-skip style, e.g. ``"half"`` or ``"full"``.
        two_side: Two-sided layout (adds ``twoside``).
        headsepline / footsepline: Draw a rule under the header / above footer.
        extra_class_options: Raw class options appended verbatim.

        head_left / head_center / head_right: Header fields (\\ihead/\\chead/\\ohead).
        foot_left / foot_center / foot_right: Footer fields (\\ifoot/\\cfoot/\\ofoot).
        clear_page_styles: Emit ``\\clearpairofpagestyles`` first (default True).
        page_style: Page style selected via ``\\pagestyle`` (default
            ``"scrheadings"``) when any header/footer is set.

        koma_fonts: Mapping of KOMA element -> font commands, each emitted as
            ``\\setkomafont{element}{commands}`` (e.g. ``{"disposition": "\\rmfamily"}``).
        subject / publishers / titlehead / dedication / extratitle: KOMA
            title-page metadata commands.
    """

    def __init__(
        self,
        content: TeX | str,
        *,
        document_class: KomaClass = "scrartcl",
        title: str | TeX | None = None,
        author: str | TeX | None = None,
        date: str | datetime | TeX | None = None,
        toc: bool = False,
        packages: set[Package | str] | None = None,
        manage_packages: bool = True,
        preamble: TeX | None = None,
        font_size: str | None = None,
        paper_size: str | None = None,
        div: DivValue | None = None,
        bcor: str | None = None,
        parskip: ParSkip | None = None,
        two_side: bool = False,
        headsepline: bool = False,
        footsepline: bool = False,
        extra_class_options: list[str] | None = None,
        head_left: TeX | str | None = None,
        head_center: TeX | str | None = None,
        head_right: TeX | str | None = None,
        foot_left: TeX | str | None = None,
        foot_center: TeX | str | None = None,
        foot_right: TeX | str | None = None,
        clear_page_styles: bool = True,
        page_style: str = "scrheadings",
        koma_fonts: Mapping[str, str] | None = None,
        subject: str | TeX | None = None,
        publishers: str | TeX | None = None,
        titlehead: str | TeX | None = None,
        dedication: str | TeX | None = None,
        extratitle: str | TeX | None = None,
    ) -> None:
        class_options = self._build_class_options(
            font_size=font_size,
            paper_size=paper_size,
            div=div,
            bcor=bcor,
            parskip=parskip,
            two_side=two_side,
            headsepline=headsepline,
            footsepline=footsepline,
            extra_class_options=extra_class_options,
        )

        preamble_parts: list[TeX] = []

        if koma_fonts:
            for element, commands in koma_fonts.items():
                preamble_parts.append(SetKomaFont(element, commands))

        for command, value in (
            (TitleHead, titlehead),
            (Subject, subject),
            (Publishers, publishers),
            (Dedication, dedication),
            (Extratitle, extratitle),
        ):
            if value is not None:
                preamble_parts.append(command(value))

        head_foot: list[tuple[type[ArgCommand], TeX | str | None]] = [
            (IHead, head_left),
            (CHead, head_center),
            (OHead, head_right),
            (IFoot, foot_left),
            (CFoot, foot_center),
            (OFoot, foot_right),
        ]
        if any(value is not None for _, value in head_foot):
            if clear_page_styles:
                preamble_parts.append(ClearPairOfPageStyles())
            for command, value in head_foot:
                if value is not None:
                    preamble_parts.append(command(value))
            preamble_parts.append(Pagestyle(page_style))

        if preamble is not None:
            preamble_parts.append(preamble)

        all_packages: set[Package | str] = set(packages) if packages else set()
        if headsepline or footsepline:
            all_packages.add(SCRLAYER_SCRPAGE)

        self._document: Document = Document(
            document_class=document_class,
            content=coerce_tex(content),
            preamble=Block(*preamble_parts) if preamble_parts else None,
            title=title,
            toc=toc,
            author=author,
            date=date,
            packages=all_packages,
            class_options=class_options,
            manage_packages=manage_packages,
        )

    @staticmethod
    def _build_class_options(
        *,
        font_size: str | None,
        paper_size: str | None,
        div: DivValue | None,
        bcor: str | None,
        parskip: ParSkip | None,
        two_side: bool,
        headsepline: bool,
        footsepline: bool,
        extra_class_options: list[str] | None,
    ) -> list[str]:
        options: list[str] = []
        if font_size is not None:
            options.append(f"fontsize={font_size}")
        if paper_size is not None:
            options.append(paper_size)
        if div is not None:
            options.append(f"DIV={div}")
        if bcor is not None:
            options.append(f"BCOR={bcor}")
        if parskip is not None:
            options.append(f"parskip={parskip}")
        if two_side:
            options.append("twoside")
        if headsepline:
            options.append("headsepline")
        if footsepline:
            options.append("footsepline")
        if extra_class_options:
            options.extend(extra_class_options)
        return options

    @property
    def document(self) -> Document:
        """The underlying :class:`pytex.Document`."""
        return self._document

    @property
    @override
    def required_packages(self) -> set[Package | str]:
        return self._document.required_packages

    @property
    @override
    def children(self) -> tuple[TeX, ...]:
        return self._document.children

    @override
    def serialize(self) -> str:
        return self._document.serialize()
