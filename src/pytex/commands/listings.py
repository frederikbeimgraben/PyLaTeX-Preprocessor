"""Factories for the `listings` package."""

from ..helpers.with_package import with_package
from ..interface.tex import TeX
from ..model.control_sequence import ControlSequence, Parameter
from ..model.environment import Environment
from ..model.raw import Raw
from ..packages import LISTINGS
from ..registry import Registry

__all__ = ["Lstdefinestyle", "Lstinline", "Lstinputlisting", "Lstlisting", "Lstset"]


def _render_value(value: object) -> str:
    """Render one listings option value.

    A TeX node renders to its LaTeX text. Every other value goes through
    `str`. The result is a plain string, so PyTeX loses the package
    requirements of a TeX value. Name those packages yourself.
    """
    if isinstance(value, TeX):
        return value.rendered
    return str(value)


def _opts_to_str(opts: dict[str, TeX | str]) -> str:
    """Join listings options into one comma-separated `key=value` string.

    Wrap a value that holds a comma or an equals sign in braces yourself.
    listings splits the string on the top-level commas.
    """
    return ",".join(f"{k}={_render_value(v)}" for k, v in opts.items())


@Registry.add
@with_package(LISTINGS)
def Lstset(options: dict[str, TeX | str]) -> TeX:
    """Render `\\lstset`, which sets the listings options for the document."""
    return ControlSequence("lstset", (Parameter(Raw(_opts_to_str(options))),))


@Registry.add
@with_package(LISTINGS)
def Lstdefinestyle(name: str, options: dict[str, TeX | str]) -> TeX:
    """Render `\\lstdefinestyle`, which defines a named listings style.

    Pass the name to a later call as the `style` option.
    """
    return ControlSequence(
        "lstdefinestyle",
        (Parameter(name), Parameter(Raw(_opts_to_str(options)))),
    )


@Registry.add
@with_package(LISTINGS)
def Lstinputlisting(path: str, options: dict[str, TeX | str] | None = None) -> TeX:
    """Render `\\lstinputlisting`, which prints a code file.

    Args:
        path: The path to the code file, relative to the rendered `.tex` file.
        options: listings options. If `options` is None, the factory renders
            no optional argument.
    """
    if options is None:
        return ControlSequence("lstinputlisting", (Parameter(path),))
    return ControlSequence(
        "lstinputlisting",
        (
            Parameter(Raw(_opts_to_str(options)), optional=True),
            Parameter(path),
        ),
    )


@Registry.add
@with_package(LISTINGS)
def Lstinline(body: str, delim: str = "|") -> TeX:
    """Render `\\lstinline`, which prints code inside a line of text.

    Args:
        body: The code to print. It must not hold the delimiter character.
        delim: The character that marks the start and the end of the code.
            The default is a vertical bar.
    """
    return Raw(f"\\lstinline{delim}{body}{delim}")


@Registry.add
@with_package(LISTINGS)
def Lstlisting(body: str, options: dict[str, TeX | str] | None = None) -> TeX:
    """Render a `lstlisting` environment, which prints a block of code.

    The factory adds no line break. listings reads the code from the line
    after `\\begin{lstlisting}`, and it needs `\\end{lstlisting}` at the start
    of a line. Start `body` with a newline and end it with a newline.

    Args:
        options: listings options. An empty dictionary gives no optional
            argument.
    """
    params: tuple[Parameter, ...] = ()
    if options:
        params = (Parameter(Raw(_opts_to_str(options)), optional=True),)
    return Environment("lstlisting", body, params)
