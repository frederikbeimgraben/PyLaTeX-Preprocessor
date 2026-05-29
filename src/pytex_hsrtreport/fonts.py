r"""Font configuration (faithful copy of ``Config/Fonts.tex``).

References ``\fontsPath`` which :func:`pytex_hsrtreport.HSRTReport` defines from
the configured assets path.
"""

FONTS = r"""\RequirePackage{lmodern}
\IfFileExists{fontspec.sty}{\RequirePackage{fontspec}}{%
  \PackageWarning{HSRTReport}{fontspec not available, using fallback fonts}}
\renewcommand*\rmdefault{lmr}
\renewcommand*\sfdefault{lmss}
\IfFileExists{fontspec.sty}{
  \IfFileExists{\fontsPath/Blender/Blender-Medium.ttf}{
    \newfontfamily\BlenderFont[
      Path=\fontsPath/Blender/, Extension=.ttf,
      UprightFont=*-Medium, BoldFont=*-Bold,
      ItalicFont=*-MediumItalic, BoldItalicFont=*-BoldItalic]{Blender}
    \renewcommand{\blenderfont}{\BlenderFont}
  }{
    \IfFontExistsTF{Blender}{\newfontfamily\BlenderFont{Blender}\renewcommand{\blenderfont}{\BlenderFont}}{
      \IfFontExistsTF{Helvetica Neue}{\newfontfamily\BlenderFont{Helvetica Neue}\renewcommand{\blenderfont}{\BlenderFont}}{
        \newfontfamily\BlenderFont{TeX Gyre Heros}\renewcommand{\blenderfont}{\BlenderFont}}}
  }
  \IfFileExists{\fontsPath/DIN/DIN-Regular.ttf}{
    \newfontfamily\DINFont[
      Path=\fontsPath/DIN/, Extension=.ttf,
      UprightFont=*-Regular, BoldFont=*-Bold,
      ItalicFont=*-Italic, BoldItalicFont=*-BoldItalic]{DIN}
    \renewcommand{\dinfont}{\DINFont}
  }{
    \IfFontExistsTF{DIN}{\newfontfamily\DINFont{DIN}\renewcommand{\dinfont}{\DINFont}}{
      \newfontfamily\DINFont{TeX Gyre Termes}\renewcommand{\dinfont}{\DINFont}}
  }
  \IfFileExists{\fontsPath/Blender/Blender-Medium.ttf}{
    \setsansfont{Blender}[
      Path=\fontsPath/Blender/, Extension=.ttf,
      UprightFont=*-Medium, BoldFont=*-Bold,
      ItalicFont=*-MediumItalic, BoldItalicFont=*-BoldItalic]
  }{
    \IfFontExistsTF{Blender}{\setsansfont{Blender}}{
      \IfFontExistsTF{Helvetica Neue}{\setsansfont{Helvetica Neue}}{\setsansfont{TeX Gyre Heros}}}
  }
  \IfFileExists{\fontsPath/DIN/DIN-Regular.ttf}{
    \setmainfont{DIN}[
      Path=\fontsPath/DIN/, Extension=.ttf,
      UprightFont=*-Regular, BoldFont=*-Bold,
      ItalicFont=*-Italic, BoldItalicFont=*-BoldItalic]
  }{
    \IfFontExistsTF{DIN}{\setmainfont{DIN}}{\setmainfont{TeX Gyre Termes}}
  }
}{
  \renewcommand*\rmdefault{lmr}
  \renewcommand*\sfdefault{lmss}
}
"""
