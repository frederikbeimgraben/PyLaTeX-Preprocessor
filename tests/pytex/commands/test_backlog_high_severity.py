"""Regression tests for the commands-latex high-severity backlog fixes."""

import pytest

from pytex.commands.builtin import Item, Itemize, Verb
from pytex.commands.captions import Captionof
from pytex.commands.definitions import Def
from pytex.commands.floats import Columnbreak, Multicols
from pytex.commands.glossaries import Newglossaryentry
from pytex.commands.listings import Lstlisting
from pytex.commands.tables import Arraystretch, Cmidrule
from pytex.packages import CAPTION


def test_itemize_with_item_body_emits_one_item_each():
    # builtin.py:385 - Item() with a body returns a Concat, not a bare
    # ControlSequence, so _is_item must recognize that shape too.
    rendered = Itemize(Item("a"), Item("b")).rendered
    assert rendered == r"\begin{itemize}\item a\item b\end{itemize}"


def test_verb_rejects_delim_inside_body():
    # builtin.py:545 - delim present in body silently produces wrong LaTeX.
    with pytest.raises(ValueError):
        Verb("a|b")


def test_verb_rejects_star_delim():
    # builtin.py:545 - delim="*" silently selects the star form of \verb.
    with pytest.raises(ValueError):
        Verb("x", delim="*")


def test_captionof_requires_caption_package():
    # captions.py:40 - \captionof comes from the caption package.
    assert CAPTION in (Captionof("figure", "text").requires or frozenset())


def _collect_requires(node):
    """Walk the node tree the way `Document.packages` does."""
    found = set(node.requires or frozenset())
    for child in node.children or ():
        found |= _collect_requires(child)
    return found


def test_def_propagates_body_package_requirement():
    # definitions.py:146 - Def must keep the body as a child node so its
    # package requirements travel to the document preamble.
    from pytex.commands.builtin import Euro
    from pytex.packages import EUROSYM

    node = Def("mycmd", Euro())
    assert node.rendered == r"\def\mycmd{\euro{}}"
    assert EUROSYM in _collect_requires(node)


def test_multicols_and_columnbreak_require_multicol():
    # floats.py:136 - Multicols/Columnbreak never named the multicol package.
    assert Multicols(2, "body").requires or frozenset()
    assert Columnbreak().requires or frozenset()


def test_lstlisting_puts_code_after_the_begin_line():
    # listings.py:96 - the code must not sit on the \begin line.
    rendered = Lstlisting("print(1)").rendered
    assert rendered.startswith("\\begin{lstlisting}\n")
    assert rendered.endswith("\n\\end{lstlisting}")


def test_cmidrule_trim_uses_parentheses():
    # tables.py:90 - booktabs reads (lr) as the trim spec, not [lr].
    assert Cmidrule("2-3", trim="lr").rendered == r"\cmidrule(lr){2-3}"


def test_arraystretch_renews_the_macro():
    # tables.py:105 - \arraystretch{1.5} prints "1.5" as text instead of
    # redefining the macro.
    assert Arraystretch("1.5").rendered == r"\renewcommand{\arraystretch}{1.5}"


def test_newglossaryentry_wraps_comma_holding_values_in_braces():
    # test_new_modules.py:257 - the existing test never exercises the
    # brace-wrapping guard with a value that holds a comma.
    rendered = Newglossaryentry(
        "acr",
        {"name": "GmbH", "description": "Gesellschaft, mit beschraenkter Haftung"},
    ).rendered
    assert rendered == (
        r"\newglossaryentry{acr}{name={GmbH},"
        r"description={Gesellschaft, mit beschraenkter Haftung}}"
    )
