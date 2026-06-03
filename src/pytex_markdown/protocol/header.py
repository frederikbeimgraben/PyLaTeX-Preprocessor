"""The compact protocol header block rendered at the top of a protocol.

Maps the parsed frontmatter to a single HSRT-styled box: meeting body + date
on top, then the organisational fields and the attendance lists. German labels
throughout (STUPA/AStA context).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, override

from pytex.commands.builtin import Textbf
from pytex.commands.fontawesome import FaIcon
from pytex.helpers.sanitize import escape_latex
from pytex.interface.tex import TeX
from pytex.model.concat import Concat
from pytex.model.raw import Raw
from pytex.registry import Registry
from pytex_hsrtreport.boxes import ColoredBox

if TYPE_CHECKING:
    from collections.abc import Iterator, Mapping

    from ..frontmatter import FrontmatterValue

__all__ = ["ProtocolHeader", "header_from_meta"]

# Frontmatter key -> human label for the single-value organisational fields.
_FIELD_LABELS: tuple[tuple[str, str], ...] = (
    ("ort", "Ort"),
    ("sitzungsleitung", "Sitzungsleitung"),
    ("protokoll", "Protokoll"),
)
# Frontmatter key -> label for the attendance lists (rendered with a count).
_LIST_LABELS: tuple[tuple[str, str], ...] = (
    ("anwesend", "Anwesend"),
    ("entschuldigt", "Entschuldigt"),
    ("abwesend", "Abwesend"),
    ("gaeste", "Gäste"),
)


def _as_list(value: FrontmatterValue | None) -> list[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    return [v.strip() for v in value.split(",") if v.strip()]


def _line(label: str, value: str) -> TeX:
    return Concat(Textbf(f"{label}: "), Raw(escape_latex(value)))


@Registry.add
@dataclass(frozen=True)
class ProtocolHeader(TeX):
    """A compact meeting-header box: title, date/time, fields, attendance."""

    gremium: str = ""
    datum: str = ""
    beginn: str = ""
    ende: str = ""
    fields: Mapping[str, str] = field(default_factory=dict[str, str])
    attendance: Mapping[str, list[str]] = field(default_factory=dict[str, list[str]])
    _parent: TeX | None = field(default=None, init=False, compare=False, repr=False)

    @property
    def title(self) -> str:
        body = self.gremium.strip()
        return f"{body} — Protokoll" if body else "Protokoll"

    def _datetime_line(self) -> str | None:
        when = " – ".join(t for t in (self.beginn, self.ende) if t)  # noqa: RUF001
        parts = ", ".join(p for p in (self.datum, when) if p)
        return parts or None

    def _lines(self) -> Iterator[TeX]:
        yield Textbf(Raw(escape_latex(self.title)))
        dt = self._datetime_line()
        if dt:
            yield _line("Datum", dt)
        for key, label in _FIELD_LABELS:
            value = self.fields.get(key, "")
            if value:
                yield _line(label, value)
        for key, label in _LIST_LABELS:
            people = self.attendance.get(key) or []
            if people:
                yield _line(f"{label} ({len(people)})", ", ".join(people))

    @property
    @override
    def rendered(self) -> str:
        body = Concat(*_intersperse(self._lines(), Raw(r"\\")))
        return ColoredBox(
            body=body,
            icon=FaIcon("users"),
            icon_color="hanblue",
            icon_size="26pt",
            background_color="hanblue",
        ).rendered


def _intersperse(items: Iterator[TeX], sep: TeX) -> Iterator[TeX]:
    for i, item in enumerate(items):
        if i:
            yield sep
        yield item


def header_from_meta(meta: Mapping[str, FrontmatterValue]) -> ProtocolHeader:
    """Build a `ProtocolHeader` from parsed frontmatter (German keys, aliases)."""

    def scalar(*keys: str) -> str:
        for key in keys:
            value = meta.get(key)
            if isinstance(value, str) and value:
                return value
        return ""

    fields = {key: scalar(key) for key, _ in _FIELD_LABELS if scalar(key)}
    attendance = {
        key: _as_list(meta.get(key))
        for key, _ in _LIST_LABELS
        if _as_list(meta.get(key))
    }
    # `gäste` is the natural German spelling; accept it as an alias for `gaeste`.
    if "gaeste" not in attendance and _as_list(meta.get("gäste")):
        attendance["gaeste"] = _as_list(meta.get("gäste"))
    return ProtocolHeader(
        gremium=scalar("gremium", "gremium"),
        datum=scalar("datum", "date"),
        beginn=scalar("beginn", "start"),
        ende=scalar("ende", "end"),
        fields=fields,
        attendance=attendance,
    )
