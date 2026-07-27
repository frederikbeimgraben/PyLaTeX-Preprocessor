import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

import pytex  # noqa: F401,E402  (populate Registry)
import pytex_components  # noqa: F401,E402
import pytex_hsrtreport  # noqa: F401,E402
import pytex_koma  # noqa: F401,E402
import pytex_markdown.protocol  # noqa: F401,E402
import pytex_tikz.tikz  # noqa: F401,E402

# The `tex(t"...")` tests use PEP 750 syntax. Python 3.13 and earlier cannot
# parse that syntax and raise SyntaxError on import. On such a Python,
# `collect_ignore_glob` keeps the file out of collection.
collect_ignore_glob: list[str] = []
if sys.version_info < (3, 14):
    collect_ignore_glob.append("pytex/test_template.py")
