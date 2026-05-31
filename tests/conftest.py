import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

import pytex  # noqa: F401,E402  (populate Registry)
import pytex_koma  # noqa: F401,E402
import pytex_tikz.tikz  # noqa: F401,E402
