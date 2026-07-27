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
    """A whole LaTeX document, from `\\documentclass` to `\\end{document}`.

    `rendered` puts the parts in this order: the document class, the packages
    in load order, one `filecontents*` block per inline image, then `preamble`.
    The `body` goes inside the `document` environment.

    Attributes:
        extra_packages: Packages to load that no node in the node tree
            requires.
    """

    body: TeX | str
    document_class: str = "article"
    document_class_options: set[PackageOption] = field(default_factory=set)
    preamble: TeX | str = Empty
    extra_packages: frozenset[PackageProtocol] = field(default_factory=frozenset)
    _parent: "TeX | None" = field(default=None, init=False, compare=False, repr=False)

    def __post_init__(self) -> None:
        attach(self, self.body, self.preamble)

    @property
    @override
    def children(self) -> tuple[TeX, ...]:
        return (coerce_tex(self.preamble), coerce_tex(self.body))

    @property
    def packages(self) -> frozenset[PackageProtocol]:
        """Every package requirement in the node tree, plus `extra_packages`.

        For each requirement the set also holds the packages that the
        requirement names in its own `after` set.
        """

        def add_with_after(pkg: PackageProtocol, found: set[PackageProtocol]) -> None:
            if pkg in found:
                return
            found.add(pkg)
            for after in pkg.after:
                add_with_after(after, found)

        def get_packages(obj: TeX, found: set[PackageProtocol]) -> None:
            for pkg in obj.requires or set[PackageProtocol]():
                add_with_after(pkg, found)

            for child in obj.children or ():
                get_packages(child, found)

        found = set[PackageProtocol]()

        get_packages(coerce_tex(self.body), found)
        get_packages(coerce_tex(self.preamble), found)

        return frozenset(found | self.extra_packages)

    def ordered_packages(self) -> tuple[PackageProtocol, ...]:
        """Sort the packages into an order that LaTeX accepts.

        A frozenset has no stable order, but LaTeX needs some packages in a
        fixed order. For example, `cleveref` must load after `hyperref`. Each
        package names that constraint in its `after` set. A depth-first
        topological sort makes the order. Ties break by name, so two runs give
        the same order.
        """
        packages = self.packages
        by_name = {p.name: p for p in packages}
        state: dict[str, bool] = {}  # name -> finished?
        out: list[PackageProtocol] = []

        def visit(pkg: PackageProtocol) -> None:
            if state.get(pkg.name) is not None:
                return  # Finished, or in progress. The second case cuts a cycle.
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
        """Write the inline images to disk under `target_dir`.

        The method converts an SVG source to PDF first. `rendered` names each
        inline image by its own resolved path, so an absolute resolved path
        writes to that same absolute path. A relative resolved path writes
        under `target_dir`, since `rendered` also names it as relative.

        Returns:
            The path of each file written, in the order of the node tree.
        """
        from pathlib import Path

        written: list[str] = []
        base = Path(target_dir)
        for img in self.inline_images:
            img.ensure_converted()
            resolved = img.resolved_path
            dest = resolved if resolved.is_absolute() else base / resolved
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_bytes(img.read_bytes())
            written.append(dest.as_posix())
        return tuple(written)

    @property
    def inline_image_block(self) -> TeX:
        """One `filecontents*` block per inline image, in node tree order."""
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
