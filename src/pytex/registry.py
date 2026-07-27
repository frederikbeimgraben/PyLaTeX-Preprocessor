"""The registry that maps a registry key to a factory or a TeX node class."""

from collections.abc import Callable
from logging import Logger
from typing import ClassVar, Self

from pytex.interface.tex import TeX

__all__ = ["Registry"]

type TeXFactory = Callable[..., TeX]

type RegistryType = type[TeX] | TeXFactory


class Registry:
    """The map from a registry key to a factory or a TeX node class.

    An inline `pytex(...)` marker runs inside this namespace, so a marker can
    call only the names in this registry. Put `@Registry.add` on a factory or
    on a node class to register it.

    The registry is class-level state that every instance shares.

    Attributes:
        types: The registry keys, mapped to their factory or node class.
        instance: The one shared instance, or None before the first
            `Registry()` call.
    """

    types: ClassVar[dict[str, RegistryType]] = {}
    instance: ClassVar[Self | None] = None

    def __new__(cls) -> Self:
        if cls.instance is None:
            cls.instance = super().__new__(cls)

        return cls.instance

    @classmethod
    def add[O: RegistryType](cls, obj: O) -> O:
        """Register `obj` under its `__name__` and return it unchanged.

        A second object with the same registry key overwrites the first one
        and logs a warning.
        """
        if (key := obj.__name__) in cls.types:
            Logger(cls.__name__).warning(
                f"Duplicate key in registry (overwritten): {key}"
            )

        cls.types[key] = obj

        return obj

    @classmethod
    def get(cls, name: str) -> RegistryType:
        """Return the factory or node class for a registry key.

        Raises:
            KeyError: No factory and no node class use this registry key.
        """
        return cls.types[name]

    @classmethod
    def has(cls, name: str) -> bool:
        return name in cls.types

    @classmethod
    def names(cls) -> frozenset[str]:
        return frozenset(cls.types.keys())

    @classmethod
    def namespace(cls) -> dict[str, RegistryType]:
        """Return a copy of the registry for use as an `eval` namespace.

        A change to the copy does not reach the registry. The copy is shallow,
        so it holds the same factory and node class objects.
        """
        return dict(cls.types)
