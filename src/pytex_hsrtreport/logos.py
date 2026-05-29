r"""Title-page and footer logos (faithful copy of ``Modules/Layout/Logos.tex``).

The original toggled the footer logos with ``\strcompare{\ShowFooterLogos}``;
here that decision is made in Python (the ``footer_logos`` flag), so only the
applicable branch is emitted. The resolved logo set is emitted as ``\AddLogo``
calls.
"""

from .variants import resolve_logos

# Array machinery, scale settings, paths, and the AddLogo command.
LOGOS_SETUP = r"""\RequirePackage{tikz}
\RequirePackage{tikzpagenodes}
\RequirePackage{graphicx}
\RequirePackage{arrayjobx}
\RequirePackage{etoolbox}
\RequirePackage{bophook}
\RequirePackage{calc}
\RequirePackage{ifthen}
\newcommand{\logosScale}{1}
\newcommand{\mainLogoScale}{1}
\newlength{\imageHeight}
\DeclareRobustCommand{\SetLogosScale}[1]{\renewcommand{\logosScale}{#1}}
\let\newglobalarray\newarray
\patchcmd{\newglobalarray}{\edef}{\xdef}{}{}
\expandarrayelementtrue
\newglobalarray\LogosPaths
\newglobalarray\LogosScales
\newcounter{logoCounter}
\setcounter{logoCounter}{0}
\DeclareRobustCommand{\AddLogo}[2]{%
\stepcounter{logoCounter}%
\LogosPaths(\thelogoCounter)={#1}%
\LogosScales(\thelogoCounter)={#2}%
\testarray{LogosPaths}(\thelogoCounter)%
\typeout{Logo \thelogoCounter: \logospath\temp@macro.pdf}%
}
\def\skylinePath{\classPath/Images/Skyline.pdf}
\def\logospath{\classPath/Images/Logos/}
\newcommand{\footerYShift}{1.5em}
\newcommand{\footerXShift}{0.7em}
\newcommand*{\IsInteger}[3]{\IfStrEq{#1}{ }{#3}{\IfInteger{#1}{#2}{#3}}}
"""

# AtBeginPage footer tikz; with/without the footer-logo foreach.
_FOOTER_LOGOS_FOREACH = r"""    \ifdefstring{\istitlepage}{\true}{}{
      \foreach \i in {1,...,\value{logoCounter}} {
        \pgfmathtruncatemacro{\prev}{\i-1}
        \node[anchor=east, inner sep=0pt, xshift=-1.5cm, yshift=2pt] (logo\i) at (logo\prev.west) {
          \makeatletter
          \testarray{LogosScales}(\i)
          \setlength{\imageHeight}{1.5cm*\real{\temp@macro}*\real{\logosScale}*\real{0.55}}
          \testarray{LogosPaths}(\i)
          \begin{tikzpicture}
            \node[] {\includegraphics[height=\imageHeight]{\logospath\temp@macro.pdf}};
          \end{tikzpicture}
          \makeatother
        };
      }
    }
"""


def at_begin_page_block(footer_logos: bool) -> str:
    """Return the ``\\AtBeginPage`` skyline/footer-logo placement."""
    foreach = _FOOTER_LOGOS_FOREACH if footer_logos else ""
    return (
        r"\AtBeginPage{"
        "\n"
        r"  \setlength{\imageHeight}{2cm*\real{\mainLogoScale}*\real{\logosScale}*\real{0.45}}"
        "\n"
        r"  \begin{tikzpicture}[overlay, remember picture]"
        "\n"
        r"    \node[anchor=south east, inner sep=0pt, xshift=-\rightmargin, yshift=\footerYShift, opacity=0.0] (logo0) at (current page.south east) {"
        "\n"
        r"      \strcompare{\thepage}{0}{}{\includegraphics[height=\imageHeight]{\imagesPath/DUMMY_FOOT.png}}"
        "\n"
        r"    };"
        "\n"
        f"{foreach}"
        r"    \node[anchor=south west, inner sep=0pt, yshift=0em] at (current page.south west) {"
        "\n"
        r"      \includegraphics[width=1.5\paperwidth]{\skylinePath}"
        "\n"
        r"    };"
        "\n"
        r"  \end{tikzpicture}"
        "\n"
        r"}"
        "\n"
    )


def add_logos_block(resolved: list[tuple[str, float]]) -> str:
    """Emit ``\\AddLogo{name}{scale}`` for each resolved logo."""
    return "\n".join(f"\\AddLogo{{{name}}}{{{scale}}}" for name, scale in resolved)


def logos_block(
    variant: str,
    logos: set[str] | list[str] | tuple[str, ...] | dict[str, float] | None,
    footer_logos: bool,
) -> str:
    """Full logo preamble: setup + AddLogo calls + footer placement."""
    resolved = resolve_logos(variant, logos)
    return "\n".join(
        (LOGOS_SETUP, add_logos_block(resolved), at_begin_page_block(footer_logos))
    )
