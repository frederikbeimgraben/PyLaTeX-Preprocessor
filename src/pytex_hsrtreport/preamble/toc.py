"""Table-of-contents tweaks (uses ``\\@dottedtocline``)."""

from pytex import IncludeTeX, TeX

from ..paths import TEX_DIR


def toc_config_block() -> TeX:
    return IncludeTeX(TEX_DIR / "toc_config.tex")


__all__ = ["toc_config_block"]
