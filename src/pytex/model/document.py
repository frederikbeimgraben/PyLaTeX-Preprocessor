from dataclasses import field
from typing import override

from pydantic.dataclasses import dataclass

from pytex.helpers.coerce import coerce_tex
from pytex.interface.package import PackageProtocol
from pytex.interface.tex import TeX
from pytex.model.concat import Concat
from pytex.model.document_class import DocumentClass
from pytex.model.empty import Empty
from pytex.model.environment import Environment


@dataclass
class Document(TeX):
    body: TeX | str
    document_class: str = "article"
    document_class_options: dict[str, str] = field(default_factory=dict)
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
