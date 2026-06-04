---
title: PyTeX Golden Report
author: Test Author
abstract: A fixed report exercising headings, lists, callouts, citations, tables, unicode, and code for golden-file regression coverage.
keywords: [pytex, golden, regression]
datalines:
  - "Version: 0.5.0"
  - "Course: Regression Testing"
classoptions: oneside
bibliography: |
  @book{knuth1984,
    author = {Knuth, Donald E.},
    title  = {The TeXbook},
    year   = {1984},
  }
  @article{einstein1905,
    author = {Einstein, Albert},
    title  = {Zur Elektrodynamik bewegter Koerper},
    year   = {1905},
  }
---

## Introduction

Body paragraph with **bold**, *emphasis*, and `inline code`.

## Lists

- alpha
- beta
  - nested gamma

1. first
2. second

## Callouts

> [!NOTE]
> An informational note.

> [!IMPORTANT]
> An important callout.

## Citation

See [@knuth1984, p. 5] and [@einstein1905].

## Table

| Name | Age | City |
|:-----|:---:|-----:|
| Bob  | 30  | NYC  |
| Ann  | 25  | LA   |

## Unicode

Price 50€, range x ≤ y ≥ z, link a ↔ b, dot a · b, flow a → b.

## Code

```python
def demo():
    return 42
```
