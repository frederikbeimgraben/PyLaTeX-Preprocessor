# pyright: reportAny=false
from collections.abc import Iterator
from dataclasses import dataclass, field

from pytex.interface.package import PackageOption
from pytex.model.document import Document
from pytex.registry import Registry

__all__ = ["KomaDocument"]

KOMA_CLASSES: frozenset[str] = frozenset(
    {"scrartcl", "scrreprt", "scrbook", "scrlttr2"}
)

PAPER_FLAGS: frozenset[str] = frozenset(
    {"a4paper", "a5paper", "b5paper", "letterpaper", "executivepaper", "legalpaper"}
)
FONTSIZE_FLAGS: frozenset[str] = frozenset({"10pt", "11pt", "12pt"})


def _on_off(value: bool, on: str, off: str) -> str:
    return on if value else off


@Registry.add
@dataclass
class KomaDocument(Document):
    document_class: str = "scrartcl"

    paper: str | None = None
    fontsize: str | None = None
    bcor: str | None = None
    div: int | str | None = None
    pagesize: str | None = None

    two_side: bool | None = None
    two_column: bool | None = None
    landscape: bool | None = None
    title_page: bool | None = None
    draft: bool | None = None

    open_at: str | None = None
    chapter_prefix: bool | None = None
    appendix_prefix: bool | None = None

    headings: str | None = None
    parskip: str | None = None
    numbers: str | None = None
    captions: str | None = None
    toc: str | None = None
    listof: str | None = None
    bibliography: str | None = None
    index: str | None = None
    footnotes: str | None = None

    head_include: bool | None = None
    foot_include: bool | None = None
    mp_include: bool | None = None

    use_geometry: bool | None = None

    extra_class_options: set[PackageOption] = field(default_factory=set)

    def __post_init__(self) -> None:
        super().__post_init__()
        if self.document_class not in KOMA_CLASSES:
            raise ValueError(
                f"Unknown KOMA-Script class {self.document_class!r}; "
                + f"expected one of {sorted(KOMA_CLASSES)}"
            )
        self.document_class_options: set[PackageOption] = (
            set(self.document_class_options)
            | set(self.extra_class_options)
            | set(self._class_option_flags())
        )

    def _class_option_flags(self) -> Iterator[PackageOption]:
        """Turn the typed KOMA fields into raw document-class options.

        Yields:
            A bare keyword such as `twoside`, or a `(key, value)` pair such
            as `("DIV", "12")`. A field that is `None` yields nothing.
        """
        # Options that carry a value. A known keyword becomes a bare flag.
        # Any other value becomes a key=value pair.
        if self.paper is not None:
            yield self.paper if self.paper in PAPER_FLAGS else ("paper", self.paper)
        if self.fontsize is not None:
            yield (
                self.fontsize
                if self.fontsize in FONTSIZE_FLAGS
                else ("fontsize", self.fontsize)
            )
        if self.bcor is not None:
            yield ("BCOR", self.bcor)
        if self.div is not None:
            yield ("DIV", str(self.div))
        if self.pagesize is not None:
            yield ("pagesize", self.pagesize)

        # Boolean toggles that map onto an on keyword and an off keyword.
        # KOMA-Script has no off keyword for `landscape`, so `landscape=False`
        # yields nothing.
        if self.two_side is not None:
            yield _on_off(self.two_side, "twoside", "oneside")
        if self.two_column is not None:
            yield _on_off(self.two_column, "twocolumn", "onecolumn")
        if self.landscape is True:
            yield "landscape"
        if self.title_page is not None:
            yield _on_off(self.title_page, "titlepage", "notitlepage")
        if self.draft is not None:
            yield _on_off(self.draft, "draft", "final")

        if self.open_at is not None:
            yield ("open", self.open_at)
        if self.chapter_prefix is not None:
            yield ("chapterprefix", _on_off(self.chapter_prefix, "true", "false"))
        if self.appendix_prefix is not None:
            yield ("appendixprefix", _on_off(self.appendix_prefix, "true", "false"))

        # Plain key=value options. The KOMA-Script key and the field have the
        # same name, so the value goes through without a change.
        for key in (
            "headings",
            "parskip",
            "numbers",
            "captions",
            "toc",
            "listof",
            "bibliography",
            "index",
            "footnotes",
        ):
            value = getattr(self, key)
            if value is not None:
                yield (key, value)

        if self.head_include is not None:
            yield "headinclude" if self.head_include else "headexclude"
        if self.foot_include is not None:
            yield "footinclude" if self.foot_include else "footexclude"
        if self.mp_include is not None:
            yield "mpinclude" if self.mp_include else "mpexclude"

        if self.use_geometry is not None:
            yield "usegeometry" if self.use_geometry else "nogeometry"
