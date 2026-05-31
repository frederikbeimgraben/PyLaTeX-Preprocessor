# pyright: reportAny=false, reportExplicitAny=false, reportUnusedParameter=false
from typing import Any, Callable, dataclass_transform


def field(
    *,
    default: Any,
    converter: Callable[[Any], Any],
) -> Any: ...


@dataclass_transform(frozen_default=True, field_specifiers=(field,), eq_default=True)
def frozen_class[T](cls: type[T]) -> type[T]: ...
