from model.base_macro import SimpleMacro

Relax = SimpleMacro("relax")()
Bold = SimpleMacro("textbf", 1)
Italic = SimpleMacro("textit", 1)

# Section headings
Section = SimpleMacro("section", 1)
Subsection = SimpleMacro("subsection", 1)
Subsubsection = SimpleMacro("subsubsection", 1)
Paragraph = SimpleMacro("paragraph", 1)
Subparagraph = SimpleMacro("subparagraph", 1)

# Links and inline code
Href = SimpleMacro("href", 2)
Texttt = SimpleMacro("texttt", 1)

# Line breaks
Newline = SimpleMacro("\\")()
