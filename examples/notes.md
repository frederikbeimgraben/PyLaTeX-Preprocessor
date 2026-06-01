# Markdown example

This file is plain Markdown. The builder converts it to native PyTeX and wraps
it in a `Document`:

    pytex examples/notes.md            # -> notes.out.tex
    pytex examples/notes.md --build     # -> build/notes.out.pdf

## Formatting

Text can be **bold**, *emphasised*, or `inline code`, with a
[link](https://tectonic-typesetting.github.io).

## Lists

- unordered item
- item with **emphasis**
  - nested item

1. first
2. second

## Code

```python
def greet(name: str) -> str:
    return f"Hello, {name}!"
```

## Callouts

GitHub-style callouts become HSRT colored boxes:

> [!NOTE]
> An informational note.

> [!TIP]
> A helpful tip.

> [!IMPORTANT]
> Something to remember.

> [!WARNING]
> Proceed with caution.
