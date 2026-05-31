from logging import Logger
from typing import Callable, ClassVar, Self

from pytex.interface.tex import TeX

type TeXFactory = Callable[..., TeX]

type RegistryType = type[TeX] | TeXFactory


class Registry:
    types: ClassVar[dict[str, RegistryType]] = dict()
    instance: ClassVar[Self | None] = None

    def __new__(cls) -> Self:
        if cls.instance is None:
            cls.instance = super(Registry, cls).__new__(cls)

        return cls.instance

    @classmethod
    def add[O: RegistryType](cls, obj: O) -> O:
        if (key := obj.__name__) in cls.types:
            Logger(cls.__name__).warning(
                f"Duplicate key in registry (overwritten): {key}"
            )

        cls.types[key] = obj

        return obj

    @classmethod
    def get(cls, name: str) -> RegistryType:
        return cls.types[name]

    @classmethod
    def has(cls, name: str) -> bool:
        return name in cls.types

    @classmethod
    def names(cls) -> frozenset[str]:
        return frozenset(cls.types.keys())

    @classmethod
    def namespace(cls) -> dict[str, RegistryType]:
        return dict(cls.types)
