from dataclasses import dataclass, field
from typing import override

from ..helpers.coerce import coerce_tex
from ..interface.package import PackageOption, PackageProtocol
from ..interface.tex import TeX
from .concat import Concat
from .document_class import DocumentClass
from .empty import Empty
from .environment import Environment


@dataclass
class Document(TeX):
    body: TeX | str
    document_class: str = "article"
    document_class_options: set[PackageOption] = field(default_factory=set)
    preamble: TeX | str = Empty
    extra_packages: frozenset[PackageProtocol] = field(default_factory=frozenset)

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
    @override
    def rendered(self) -> str:
        return Concat(
            DocumentClass(self.document_class, self.document_class_options),
            *self.packages,
            self.preamble,
            Environment("document", self.body),
        ).rendered
