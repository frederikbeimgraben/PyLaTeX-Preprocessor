from dataclasses import dataclass

type Primitive = str | int | float


@dataclass
class Macro:
    tex_id: str

    params: tuple["Macro" | Primitive, ...] | None
