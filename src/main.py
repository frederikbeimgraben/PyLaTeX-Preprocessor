#!/usr/bin/env python3
"""
Demo program for PyLaTeX - Comprehensive Type Showcase

This demonstrates all available TeX types by building a complete
document tree programmatically and serializing it to LaTeX.
"""

from model.builtins import (
    Bold,
    Href,
    Italic,
    Newline,
    Paragraph,
    Section,
    Subsection,
    Subsubsection,
    Texttt,
)
from model.environment import Enumerate, Environment, Item, Itemize, Quote, Verbatim
from model.group import Group
from model.raw import Raw


def main() -> None:
    """Build a comprehensive document tree showcasing all types"""

    print("=" * 80)
    print("PyLaTeX Comprehensive Type Showcase")
    print("=" * 80)
    print("\nBuilding document tree with all available types...\n")

    # Build the complete document tree
    document = Group(
        # Title Section
        Section(Raw("Introduction to PyLaTeX")),
        # Basic paragraph with formatting
        Paragraph(
            Group(
                Raw("This document demonstrates "),
                Bold(Raw("all available types")),
                Raw(" in the PyLaTeX system. It includes "),
                Italic(Raw("formatted text")),
                Raw(", "),
                Texttt(Raw("inline code")),
                Raw(", and much more."),
            )
        ),
        # Subsection: Text Formatting
        Subsection(Raw("Text Formatting")),
        Paragraph(
            Group(
                Raw("We support "),
                Bold(Raw("bold text")),
                Raw(", "),
                Italic(Raw("italic text")),
                Raw(", "),
                Texttt(Raw("monospace text")),
                Raw(", and even "),
                Bold(Italic(Raw("bold italic combined"))),
                Raw("!"),
            )
        ),
        # Subsection: Links
        Subsection(Raw("Hyperlinks")),
        Paragraph(
            Group(
                Raw("Visit "),
                Href(Raw("https://github.com"), Bold(Raw("GitHub"))),
                Raw(" for more information. You can also check "),
                Href(Raw("https://www.python.org"), Raw("Python.org")),
                Raw("."),
            )
        ),
        # Subsection: Lists
        Subsection(Raw("Lists and Enumerations")),
        Subsubsection(Raw("Unordered List")),
        Itemize(
            Item(Raw("First item in the list")),
            Item(Group(Raw("Second item with "), Bold(Raw("bold text")))),
            Item(
                Group(
                    Raw("Third item with "),
                    Href(Raw("https://example.com"), Raw("a link")),
                )
            ),
        ),
        Subsubsection(Raw("Ordered List")),
        Enumerate(
            Item(Raw("First step")),
            Item(Group(Raw("Second step with "), Italic(Raw("emphasis")))),
            Item(Group(Raw("Third step with "), Texttt(Raw("code")))),
        ),
        # Subsection: Block Quotes
        Subsection(Raw("Block Quotes")),
        Paragraph(Raw("As the famous saying goes:")),
        Quote(
            Group(
                Paragraph(
                    Group(
                        Italic(
                            Raw('"The best way to predict the future is to invent it."')
                        ),
                        Raw(" — Alan Kay"),
                    )
                )
            )
        ),
        # Subsection: Code Blocks
        Subsection(Raw("Code Examples")),
        Paragraph(
            Group(
                Raw("Here's an example using "),
                Texttt(Raw("verbatim")),
                Raw(" environment:"),
            )
        ),
        Verbatim("""def fibonacci(n):
    if n <= 1:
        return n
    return fibonacci(n-1) + fibonacci(n-2)

# Calculate Fibonacci numbers
for i in range(10):
    print(f"fib({i}) = {fibonacci(i)}")"""),
        # Subsection: Special Characters
        Subsection(Raw("Special Characters")),
        Paragraph(Raw("LaTeX special characters are properly escaped:")),
        Itemize(
            Item(Raw("Dollar signs: \\$100")),
            Item(Raw("Ampersands: Tom \\& Jerry")),
            Item(Raw("Percent: 100\\% complete")),
            Item(Raw("Hash: \\#hashtag")),
            Item(Raw("Underscore: variable\\_name")),
            Item(Raw("Braces: \\{curly\\} braces")),
            Item(Raw("Tilde: \\textasciitilde{}/home/user")),
            Item(Raw("Caret: 2\\textasciicircum{}10")),
        ),
        # Subsection: Nested Structures
        Subsection(Raw("Nested Structures")),
        Paragraph(Raw("Complex nesting is fully supported:")),
        Itemize(
            Item(
                Group(
                    Bold(Raw("Outer item with bold")),
                    Raw(" containing:"),
                    Itemize(
                        Item(Italic(Raw("Nested italic item"))),
                        Item(
                            Group(
                                Raw("Nested item with "),
                                Href(
                                    Raw("https://nested.example.com"),
                                    Texttt(Raw("code link")),
                                ),
                            )
                        ),
                    ),
                )
            ),
            Item(
                Group(
                    Raw("Another outer item"),
                    Enumerate(
                        Item(Raw("Nested ordered item 1")),
                        Item(Raw("Nested ordered item 2")),
                    ),
                )
            ),
        ),
        # Subsection: Custom Environments
        Subsection(Raw("Custom Environments")),
        Paragraph(Raw("You can create custom LaTeX environments:")),
        Environment(
            "center",
            Group(
                Bold(Italic(Raw("Centered and formatted text"))),
                Newline,
                Raw("This uses a custom environment"),
            ),
        ),
        # Subsection: Complex Example
        Subsection(Raw("Putting It All Together")),
        Paragraph(
            Group(
                Raw("This "),
                Bold(Raw("comprehensive example")),
                Raw(" shows how to combine "),
                Italic(Raw("all the features")),
                Raw(" together. You can visit "),
                Href(Raw("https://github.com/pylatex"), Bold(Raw("our repository"))),
                Raw(" for more examples."),
            )
        ),
        Quote(
            Group(
                Paragraph(
                    Group(
                        Raw("The combination of "),
                        Bold(Raw("Python")),
                        Raw(" and "),
                        Bold(Raw("LaTeX")),
                        Raw(
                            " provides a powerful way to generate documents programmatically."
                        ),
                    )
                )
            )
        ),
        Enumerate(
            Item(Group(Bold(Raw("Benefit 1:")), Raw(" Type-safe document generation"))),
            Item(
                Group(
                    Bold(Raw("Benefit 2:")),
                    Raw(" Programmatic control over "),
                    Italic(Raw("all elements")),
                )
            ),
            Item(
                Group(
                    Bold(Raw("Benefit 3:")),
                    Raw(" Easy integration with "),
                    Texttt(Raw("markdown")),
                    Raw(" parsing"),
                )
            ),
        ),
        # Final section
        Section(Raw("Conclusion")),
        Paragraph(
            Group(
                Raw("This document showcased "),
                Bold(Raw("all major components")),
                Raw(
                    " of the PyLaTeX system including: text formatting, links, lists, quotes, code blocks, special characters, nested structures, and custom environments."
                ),
            )
        ),
        Paragraph(Group(Italic(Raw("Thank you for exploring PyLaTeX!")))),
    )

    # Serialize the entire document tree
    print("=" * 80)
    print("SERIALIZED LaTeX OUTPUT:")
    print("=" * 80)
    print()
    print(document.serialize())
    print()

    # Save to file
    output_file = "demo_output.tex"
    with open(output_file, "w") as f:
        # Create a complete LaTeX document
        latex_content = f"""\\documentclass{{article}}
\\usepackage{{hyperref}}
\\usepackage{{fancyvrb}}
\\usepackage{{parskip}}

\\title{{PyLaTeX Type Showcase}}
\\author{{Generated Programmatically}}
\\date{{\\today}}

\\begin{{document}}

\\maketitle

\\tableofcontents
\\newpage

{document.serialize()}

\\end{{document}}"""
        f.write(latex_content)

    print("=" * 80)
    print(f"✅ Complete LaTeX document saved to: {output_file}")
    print(f"   Compile with: pdflatex {output_file}")
    print("=" * 80)
    print()


if __name__ == "__main__":
    main()
