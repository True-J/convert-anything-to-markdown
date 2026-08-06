"""Extractor implementations — one module per tool family.

All extractors implement the `Extractor` protocol from `base.py`. Lazy-import
their backing libraries so missing dependencies degrade gracefully (the
router catches ExtractorUnavailable and tries the next in the chain).
"""

from convert_anything_md.extractors.base import (
    ExtractionResult,
    Extractor,
    ExtractorError,
    ExtractorUnavailable,
)

__all__ = [
    "ExtractionResult",
    "Extractor",
    "ExtractorError",
    "ExtractorUnavailable",
]

