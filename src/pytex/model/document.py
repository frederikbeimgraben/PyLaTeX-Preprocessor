from dataclasses import dataclass, field
from typing import override

from ..helpers.coerce import coerce_tex
from ..helpers.parenting import attach
from ..interface.package import PackageOption, PackageProtocol
from ..interface.tex import TeX
from ..registry import Registry
from .concat import Concat
from .document_class import DocumentClass
from .empty import Empty
from .environment import Environment
from .image import IncludeImage, collect_inline_images, filecontents_b64_block
from .raw import Raw


@Registry.add
@dataclass
class Document(TeX):
    body: TeX | str
    document_class: str = "article"
    document_class_options: set[PackageOption] = field(default_factory=set)
    preamble: TeX | str = Empty
    extra_packages: frozenset[PackageProtocol] = field(default_factory=frozenset)
    _parent: "TeX | None" = field(default=None, init=False, compare=False, repr=False)

    def __post_init__(self) -> None:
        attach(self, self.body, self.preamble)

    @property
    def packages(self) -> frozenset[PackageProtocol]:
        def get_packages(obj: TeX, found: set[PackageProtocol]) -> None:
            found |= obj.requires or set()

            for child in obj.children or tuple():
                get_packages(child, found)

        found = set[PackageProtocol]()

        get_packages(coerce_tex(self.body), found)
        get_packages(coerce_tex(self.preamble), found)

        return frozenset(found | self.extra_packages)

    @property
    def inline_images(self) -> tuple[IncludeImage, ...]:
        images: dict[str, IncludeImage] = {}
        for root in (self.body, self.preamble):
            for img in collect_inline_images(coerce_tex(root)):
                key = img.resolved_path.as_posix()
                images.setdefault(key, img)
        return tuple(images.values())

    def write_inline_images(self, target_dir: str = ".") -> tuple[str, ...]:
        """Materialise inline images to disk relative to `target_dir`. Returns paths."""
        from pathlib import Path

        written: list[str] = []
        base = Path(target_dir)
        for img in self.inline_images:
            img.ensure_converted()
            resolved = img.resolved_path
            rel = Path(*resolved.parts[1:]) if resolved.is_absolute() else resolved
            dest = base / rel
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_bytes(img.read_bytes())
            written.append(dest.as_posix())
        return tuple(written)

    @property
    def inline_image_block(self) -> TeX:
        """`\\begin{filecontents*}` for each inline image, in tree order."""
        images = self.inline_images
        if not images:
            return Empty
        return Concat(*(Raw(filecontents_b64_block(img)) for img in images))

    @property
    @override
    def rendered(self) -> str:
        return Concat(
            DocumentClass(self.document_class, self.document_class_options),
            *self.packages,
            self.inline_image_block,
            self.preamble,
            Environment("document", self.body),
        ).rendered
