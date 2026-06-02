import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

import pytex  # noqa: F401,E402  (populate Registry)
import pytex_hsrtreport  # noqa: F401,E402
import pytex_koma  # noqa: F401,E402
import pytex_protocol  # noqa: F401,E402
import pytex_tikz.tikz  # noqa: F401,E402

# `tex(t"...")` tests use PEP 750 syntax that does not parse before 3.14; skip
# collecting them (importing the file would raise SyntaxError) on older Pythons.
collect_ignore_glob: list[str] = []
if sys.version_info < (3, 14):
    collect_ignore_glob.append("pytex/test_template.py")
