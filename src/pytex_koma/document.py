# pyright: reportAny=false
from dataclasses import dataclass, field

from pytex.interface.package import PackageOption
from pytex.model.document import Document
from pytex.registry import Registry

KOMA_CLASSES: frozenset[str] = frozenset(
    {"scrartcl", "scrreprt", "scrbook", "scrlttr2"}
)

_PAPER_FLAGS: frozenset[str] = frozenset(
    {"a4paper", "a5paper", "b5paper", "letterpaper", "executivepaper", "legalpaper"}
)
_FONTSIZE_FLAGS: frozenset[str] = frozenset({"10pt", "11pt", "12pt"})


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

        opts: set[PackageOption] = set(self.document_class_options) | set(
            self.extra_class_options
        )

        if self.paper is not None:
            opts.add(
                self.paper if self.paper in _PAPER_FLAGS else ("paper", self.paper)
            )
        if self.fontsize is not None:
            opts.add(
                self.fontsize
                if self.fontsize in _FONTSIZE_FLAGS
                else ("fontsize", self.fontsize)
            )
        if self.bcor is not None:
            opts.add(("BCOR", self.bcor))
        if self.div is not None:
            opts.add(("DIV", str(self.div)))
        if self.pagesize is not None:
            opts.add(("pagesize", self.pagesize))

        if self.two_side is not None:
            opts.add(_on_off(self.two_side, "twoside", "oneside"))
        if self.two_column is not None:
            opts.add(_on_off(self.two_column, "twocolumn", "onecolumn"))
        if self.landscape is True:
            opts.add("landscape")
        if self.title_page is not None:
            opts.add(_on_off(self.title_page, "titlepage", "notitlepage"))
        if self.draft is not None:
            opts.add(_on_off(self.draft, "draft", "final"))

        if self.open_at is not None:
            opts.add(("open", self.open_at))
        if self.chapter_prefix is not None:
            opts.add(("chapterprefix", _on_off(self.chapter_prefix, "true", "false")))
        if self.appendix_prefix is not None:
            opts.add(("appendixprefix", _on_off(self.appendix_prefix, "true", "false")))

        for attr, key in (
            ("headings", "headings"),
            ("parskip", "parskip"),
            ("numbers", "numbers"),
            ("captions", "captions"),
            ("toc", "toc"),
            ("listof", "listof"),
            ("bibliography", "bibliography"),
            ("index", "index"),
            ("footnotes", "footnotes"),
        ):
            value = getattr(self, attr)
            if value is not None:
                opts.add((key, value))

        if self.head_include is not None:
            opts.add("headinclude" if self.head_include else "headexclude")
        if self.foot_include is not None:
            opts.add("footinclude" if self.foot_include else "footexclude")
        if self.mp_include is not None:
            opts.add("mpinclude" if self.mp_include else "mpexclude")

        if self.use_geometry is not None:
            opts.add("usegeometry" if self.use_geometry else "nogeometry")

        self.document_class_options: set[PackageOption] = opts
