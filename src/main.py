#!/usr/bin/env python3
"""
Demo program for PyLaTeX Markdown Parser

This demonstrates the conversion of Markdown to LaTeX using the
markdown parsing functionality.
"""

import marko

from model.markdown import parse_md


def print_section(title: str) -> None:
    """Print a section header"""
    print("\n" + "=" * 80)
    print(f" {title}")
    print("=" * 80)


def demo_basic_formatting() -> None:
    """Demonstrate basic text formatting"""
    print_section("1. Basic Text Formatting")

    markdown = """
This is a paragraph with **bold text**, *italic text*, and `inline code`.

You can also combine formatting like ***bold and italic*** together.
"""

    print("\n📝 Markdown Input:")
    print(markdown)

    doc = marko.parse(markdown)
    result = parse_md(doc)

    print("\n📄 LaTeX Output:")
    print(result.serialize())


def demo_headings() -> None:
    """Demonstrate heading levels"""
    print_section("2. Headings")

    markdown = """
# Main Title (H1)

## Section (H2)

### Subsection (H3)

#### Sub-subsection (H4)

##### Paragraph (H5)

###### Subparagraph (H6)
"""

    print("\n📝 Markdown Input:")
    print(markdown)

    doc = marko.parse(markdown)
    result = parse_md(doc)

    print("\n📄 LaTeX Output:")
    print(result.serialize())


def demo_lists() -> None:
    """Demonstrate lists"""
    print_section("3. Lists")

    markdown = """
## Unordered List

- First item
- Second item
- Third item with **bold text**

## Ordered List

1. First step
2. Second step
3. Third step with *emphasis*

## Nested Lists

- Outer item 1
  - Nested item 1.1
  - Nested item 1.2
- Outer item 2
"""

    print("\n📝 Markdown Input:")
    print(markdown)

    doc = marko.parse(markdown)
    result = parse_md(doc)

    print("\n📄 LaTeX Output:")
    print(result.serialize())


def demo_code_blocks() -> None:
    """Demonstrate code blocks"""
    print_section("4. Code Blocks")

    markdown = """
Here's some inline code: `print("Hello, World!")`

And here's a code block:

```python
def fibonacci(n):
    if n <= 1:
        return n
    return fibonacci(n-1) + fibonacci(n-2)

# Calculate the 10th Fibonacci number
result = fibonacci(10)
print(f"Result: {result}")
```

Indented code also works:

    for i in range(5):
        print(i)
"""

    print("\n📝 Markdown Input:")
    print(markdown)

    doc = marko.parse(markdown)
    result = parse_md(doc)

    print("\n📄 LaTeX Output:")
    print(result.serialize())


def demo_links() -> None:
    """Demonstrate links"""
    print_section("5. Links and URLs")

    markdown = """
Visit [GitHub](https://github.com) for more information.

You can also use autolinks: <https://www.python.org>

Links can have [**formatted text**](https://example.com) too!
"""

    print("\n📝 Markdown Input:")
    print(markdown)

    doc = marko.parse(markdown)
    result = parse_md(doc)

    print("\n📄 LaTeX Output:")
    print(result.serialize())


def demo_quotes() -> None:
    """Demonstrate blockquotes"""
    print_section("6. Block Quotes")

    markdown = """
As someone once said:

> This is a blockquote.
> It can span multiple lines.
>
> And even have **formatted** text!
"""

    print("\n📝 Markdown Input:")
    print(markdown)

    doc = marko.parse(markdown)
    result = parse_md(doc)

    print("\n📄 LaTeX Output:")
    print(result.serialize())


def demo_special_characters() -> None:
    """Demonstrate special character escaping"""
    print_section("7. Special Character Escaping")

    markdown = """
LaTeX special characters are automatically escaped:

- Dollar signs: $100
- Ampersands: Tom & Jerry
- Percent signs: 100% complete
- Hash symbols: #hashtag
- Underscores: variable_name
- Curly braces: {this} and {that}
- Tilde: ~/home/user
- Caret: 2^10
"""

    print("\n📝 Markdown Input:")
    print(markdown)

    doc = marko.parse(markdown)
    result = parse_md(doc)

    print("\n📄 LaTeX Output:")
    print(result.serialize())


def demo_complex_document() -> None:
    """Demonstrate a complete complex document"""
    print_section("8. Complex Document")

    markdown = """
# Research Paper: Machine Learning

## Abstract

This paper explores the fundamentals of **machine learning** and its applications in modern computing.

## Introduction

Machine learning (ML) is a subset of *artificial intelligence* that focuses on:

1. Data analysis
2. Pattern recognition
3. Predictive modeling

### Historical Context

> "Machine learning is the science of getting computers to act without being explicitly programmed."
> — Andrew Ng

## Methodology

Our approach consists of three main steps:

- **Data Collection**: Gathering relevant datasets
- **Model Training**: Using algorithms like:
  1. Linear Regression
  2. Decision Trees
  3. Neural Networks
- **Evaluation**: Testing model accuracy

### Code Example

Here's a simple implementation:

```python
import numpy as np

def train_model(X, y):
    # Training logic
    weights = np.random.randn(X.shape[1])
    return weights
```

## Results

We achieved an accuracy of 95% on the test dataset. For more details, visit our [GitHub repository](https://github.com/example/ml-project).

### Performance Metrics

- Precision: 0.94
- Recall: 0.96
- F1-Score: 0.95

## Conclusion

Machine learning continues to revolutionize various industries. Key takeaways:

1. Data quality is crucial
2. Model selection depends on the problem
3. Continuous evaluation is necessary

---

*Thank you for reading!*
"""

    print("\n📝 Markdown Input:")
    print(markdown)

    doc = marko.parse(markdown)
    result = parse_md(doc)

    print("\n📄 LaTeX Output:")
    print(result.serialize())


def demo_latex_document() -> None:
    """Generate a complete LaTeX document"""
    print_section("9. Complete LaTeX Document Generation")

    markdown = """
# Introduction to Python

Python is a **high-level**, *general-purpose* programming language.

## Key Features

1. Easy to learn
2. Powerful libraries
3. Cross-platform support

## Example Code

```python
def greet(name):
    return f"Hello, {name}!"

print(greet("World"))
```

Visit [Python.org](https://www.python.org) for more information.
"""

    print("\n📝 Markdown Input:")
    print(markdown)

    doc = marko.parse(markdown)
    result = parse_md(doc)

    # Wrap in a complete LaTeX document
    latex_document = f"""\\documentclass{{article}}
\\usepackage{{hyperref}}
\\usepackage{{fancyvrb}}

\\title{{Python Programming Guide}}
\\author{{Generated from Markdown}}
\\date{{\\today}}

\\begin{{document}}

\\maketitle

{result.serialize()}

\\end{{document}}"""

    print("\n📄 Complete LaTeX Document:")
    print(latex_document)

    # Optionally save to file
    output_file = "output.tex"
    with open(output_file, "w") as f:
        f.write(latex_document)
    print(f"\n✅ LaTeX document saved to: {output_file}")


def main() -> None:
    """Main demo function"""
    print("\n" + "🚀" * 40)
    print("  PyLaTeX Markdown Parser - Demonstration")
    print("🚀" * 40)

    demos = [
        demo_basic_formatting,
        demo_headings,
        demo_lists,
        demo_code_blocks,
        demo_links,
        demo_quotes,
        demo_special_characters,
        demo_complex_document,
        demo_latex_document,
    ]

    print("\n📚 This demo showcases the markdown to LaTeX conversion capabilities.")
    print("   Each section demonstrates different markdown features.\n")

    try:
        for i, demo in enumerate(demos, 1):
            demo()

            # Pause between demos (except for the last one)
            if i < len(demos):
                input("\n⏸️  Press Enter to continue to the next demo...")

    except KeyboardInterrupt:
        print("\n\n❌ Demo interrupted by user.")
        return

    print("\n" + "=" * 80)
    print("✨ Demo complete! Check 'output.tex' for a complete LaTeX document.")
    print("=" * 80 + "\n")


if __name__ == "__main__":
    main()
