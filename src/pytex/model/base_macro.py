from collections.abc import Mapping
from typing import ClassVar, Protocol, override

from .base_model import TeX
from .helpers import BACKSLASH, CLOSING_BRACE, OPENING_BRACE
from .raw import coerce_tex


class BaseMacro(TeX, Protocol):
    MACRO_ID: ClassVar[str] = ""
    N_POSITIONAL: ClassVar[int] = 0
    KEYWORD_ARGS: ClassVar[Mapping[str, tuple[type[TeX], TeX]]] = {}

    _args: tuple["TeX", ...] | None = None
    _kwargs: Mapping[str, "TeX"] | None = None

    @property
    def id(self) -> str:
        return self.MACRO_ID

    @property
    def n_positional(self) -> int:
        return self.N_POSITIONAL

    @property
    def keyword_args(self) -> dict[str, tuple[type[TeX], TeX]]:
        return dict(self.KEYWORD_ARGS)

    @property
    def args(self) -> tuple["TeX", ...]:
        return self._args if self._args is not None else tuple()

    @property
    def kwargs(self) -> Mapping[str, "TeX"]:
        return self._kwargs if self._kwargs is not None else dict()

    @override
    def __init__(self, *args: TeX | str, **kwargs: TeX | str) -> None:
        coerced_args = tuple(coerce_tex(a) for a in args)
        coerced_kwargs: dict[str, TeX] = {k: coerce_tex(v) for k, v in kwargs.items()}

        if not len(coerced_args) == self.n_positional:
            raise ValueError(
                f"Invalid parameter count: {len(coerced_args)} != {self.n_positional}!"
            )

        last_key: str = ""
        last_value: TeX | None = None

        if any(
            (last_key := key) not in self.keyword_args
            or not isinstance((last_value := value), self.keyword_args[key][0])
            for key, value in coerced_kwargs.items()
        ):
            if last_key not in self.keyword_args:
                raise ValueError(
                    f"Key {last_key} is not allowed for Macro {BACKSLASH}{self.id}!"
                )
            else:
                raise ValueError(
                    f"Value type {type(last_value)} is not allowed for key {last_key}: {type(last_value)} is no subtype of {self.keyword_args[last_key][0]}"
                )

        for key, (_, default) in self.keyword_args.items():
            if key not in coerced_kwargs:
                coerced_kwargs[key] = default

        self._args = coerced_args
        self._kwargs = coerced_kwargs

    @property
    @override
    def children(self) -> tuple["TeX", ...]:
        return self.args

    @override
    def serialize(self, indent: int = 0) -> str:
        """Serialize with optional indentation.

        Args:
            indent: Indentation level (default: 0)

        Returns:
            Serialized LaTeX string
        """
        return self.serialize_indented(indent)

    def serialize_indented(self, indent: int) -> str:
        """Serialize with indentation.

        Args:
            indent: Indentation level

        Returns:
            Serialized LaTeX string
        """
        from .serialization import serialize_with_indent

        kwargs = ",".join(
            f"{key}={serialize_with_indent(value, 0)}"
            for key, value in self.kwargs.items()
        )
        args = "".join(
            f"{OPENING_BRACE}{serialize_with_indent(value, 0)}{CLOSING_BRACE}"
            for value in self.args
        )

        kwargs_part = f"[{kwargs}]" if len(kwargs) != 0 else ""
        # Always add a space after macros to ensure proper spacing
        # LaTeX will collapse multiple consecutive spaces into one
        return f"\\{self.id}{kwargs_part}{args}\\relax "
