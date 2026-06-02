---
title: PyTeX Report Example
author: Frederik Beimgraben
classoptions: [11pt, oneside]
---

## Frontmatter

The `report` variant reads three frontmatter fields (each with a German
alias, and `--config` JSON overrides any of them):

| Field | Alias | Meaning |
|:------|:------|:--------|
| `title` | `titel` | title-page title; falls back to the first `#` heading |
| `author` | `autor` | title-page author |
| `classoptions` | `class_options` | KOMA class options (list, `a=b` map, or comma string) |

Build it with:

```sh
pytex examples/report.md --variant report            # -> report.out.tex
pytex examples/report.md --variant report --build    # -> build/report.out.pdf
```

> [!NOTE]
> When `title`/`titel` is omitted, the first `#` heading becomes the title and
> is re-emitted in the body as a big, unnumbered heading.

## Formatting

Text can be **bold**, *emphasised*, or `inline code`. External links stay
clickable ([Tectonic](https://tectonic-typesetting.github.io)), while relative
links such as [`LICENSE`](LICENSE) keep their text only (they have no target in
a PDF).

ASCII arrows in prose become math arrows: a -> b, b <- a, a <-> b, p => q,
p <=> q, and the long forms a --> b, a <-- b, a <--> b. (Arrows inside `code`
are left untouched.)

## Tables

Wide tables wrap inside the text width (`tabularx`) instead of overflowing:

| Stage | Command | Notes |
|:------|:--------|------:|
| parse | `marko` | GitHub-flavoured Markdown, including pipe tables |
| convert | `MarkdownConverter` | walks the AST into native PyTeX nodes |
| render | `.rendered` | emits LaTeX that compiles with tectonic |

## Code

Long lines wrap (`lstlisting` with `breaklines`):

```python
def greet(name: str) -> str:
    return f"Hello, {name}! This line is intentionally long so it demonstrates that listings wrap instead of running off the page."
```

## Images

Images are included with `\includegraphics`; run from the repository root so
the relative path resolves:

![HSRT logo](examples/example-image.pdf)

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
