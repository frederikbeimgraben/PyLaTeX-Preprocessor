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

__all__ = ["Document"]


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
            found |= {
                after
                for pkg in (obj.requires or set[PackageProtocol]())
                for after in pkg.after | {pkg}
            }

            for child in obj.children or ():
                get_packages(child, found)

        found = set[PackageProtocol]()

        get_packages(coerce_tex(self.body), found)
        get_packages(coerce_tex(self.preamble), found)

        return frozenset(found | self.extra_packages)

    def ordered_packages(self) -> tuple[PackageProtocol, ...]:
        """Packages sorted so each is emitted after its `after` dependencies.

        A frozenset has no stable order, but some packages must be loaded in a
        fixed sequence (e.g. `cleveref` after `hyperref`). Resolve that with a
        depth-first topological sort, breaking ties by name for reproducibility.
        """
        packages = self.packages
        by_name = {p.name: p for p in packages}
        state: dict[str, bool] = {}  # name -> finished?
        out: list[PackageProtocol] = []

        def visit(pkg: PackageProtocol) -> None:
            if state.get(pkg.name) is not None:
                return  # finished, or currently visiting (cycle guard)
            state[pkg.name] = False
            for dep in sorted(pkg.after or (), key=lambda d: d.name):
                present = by_name.get(dep.name)
                if present is not None:
                    visit(present)
            state[pkg.name] = True
            out.append(pkg)

        for pkg in sorted(packages, key=lambda p: p.name):
            visit(pkg)
        return tuple(out)

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
            *self.ordered_packages(),
            self.inline_image_block,
            self.preamble,
            Environment("document", self.body),
        ).rendered
