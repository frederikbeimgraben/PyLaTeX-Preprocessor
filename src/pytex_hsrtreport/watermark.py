"""Page watermark — diagonal repeated text built from native pytex.

The watermark text is supplied by the Python caller and baked into a
``\\DraftwatermarkOptions{...}`` invocation. The tile body uses
:class:`BeginAccSupp`, :class:`Whiledo` and pgffor's ``\\foreach`` column
loop so accessibility metadata stays attached to every glyph.
"""

from dataclasses import dataclass
from typing import override

from pytex import (
    BeginAccSupp,
    BuiltinPackages,
    Command,
    NewCounter,
    Newline,
    Package,
    SetCounter,
    TabularEnv,
    TeX,
    Whiledo,
)
from pytex.model.raw import coerce_tex
from pytex_komascript.model import Block


def _tile_body(text: str) -> TeX:
    """One run of 16 tiles laid out by pgffor's ``\\foreach``."""
    return Block(
        Command("foreach", coerce_tex("\\col in {0,...,15}")),
        Command("color", "black!5"),
        BeginAccSupp(coerce_tex(f"{text}~~"), actual_text=""),
    )


@dataclass(init=False)
class DraftwatermarkOptions(TeX):
    """``\\DraftwatermarkOptions{key=val,...}`` from ``draftwatermark``.

    The ``text`` is baked into a ``tabular`` + ``\\whiledo`` body so the
    tile fills the page; accessibility wrapping comes from
    :class:`pytex.BeginAccSupp`.
    """

    scale: float
    angle: float
    color: str
    text: str

    def __init__(
        self,
        *,
        scale: float = 0.08,
        angle: float = 45,
        color: str = "black!12",
        text: str = "",
    ) -> None:
        self.scale = scale
        self.angle = angle
        self.color = color
        self.text = text

    @property
    @override
    def required_packages(self) -> set[Package | str]:
        return {BuiltinPackages.DRAFTWATERMARK.value}

    @property
    @override
    def children(self) -> tuple[TeX, ...]:
        return ()

    def _body(self) -> TeX:
        loop = Block(
            SetCounter("it", 1),
            Whiledo(
                "\\theit<100",
                Block(
                    _tile_body(self.text),
                    Newline,
                    Command("stepcounter", "it"),
                ),
            ),
        )
        return TabularEnv("c", loop)

    @override
    def serialize(self) -> str:
        body = self._body().serialize()
        return (
            "\\DraftwatermarkOptions{"
            f"scale={self.scale},angle={self.angle},"
            f"text={{{body}}},"
            f"color={self.color}"
            "}"
        )


def watermark_block(text: str = "") -> TeX:
    """Counter declaration + ``DraftwatermarkOptions`` with ``text`` baked in.

    When ``text`` is empty the options are still emitted so the package sees a
    well-formed configuration; just no visible glyphs end up on the page.
    """
    return Block(
        NewCounter("it"),
        DraftwatermarkOptions(text=text),
    )


__all__ = ["DraftwatermarkOptions", "watermark_block"]
