"""Fallback PDF / Office extractor: Microsoft MarkItDown.

Broader format coverage than docling (handles DOC, TXT, HTML, and more)
and much faster because it doesn't load ML models. Used as the first
fallback when docling is missing or fails, and as the primary path for
formats docling doesn't support well (HTML).
"""

from __future__ import annotations

import time
from pathlib import Path

from convert_anything_md.extractors.base import (
    ExtractionResult,
    ExtractorError,
    ExtractorUnavailable,
    word_count,
)


class MarkItDownExtractor:
    """MarkItDown wrapper — works on PDF, DOCX, PPTX, XLSX, HTML, audio, …"""

    name = "markitdown"

    def extract(self, path: Path) -> ExtractionResult:
        try:
            from markitdown import MarkItDown
        except ImportError as exc:
            raise ExtractorUnavailable(
                "markitdown is not installed (pip install 'markitdown[all]')"
            ) from exc

        start = time.perf_counter()
        try:
            md = MarkItDown(enable_plugins=False)
            result = md.convert(str(path))
        except Exception as exc:  # noqa: BLE001 - MarkItDown raises many types
            raise ExtractorError(f"markitdown failed on {path.name}: {exc}") from exc

        text_content = getattr(result, "text_content", None) or getattr(
            result, "markdown", ""
        )
        if not text_content:
            raise ExtractorError(
                f"markitdown returned no content for {path.name}"
            )

        duration_ms = int((time.perf_counter() - start) * 1000)
        return ExtractionResult(
            markdown=text_content.strip() + "\n",
            engine=self.name,
            word_count=word_count(text_content),
            duration_ms=duration_ms,
            fallback_chain=[self.name],
        )

