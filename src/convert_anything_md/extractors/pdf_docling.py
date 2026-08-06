"""Primary PDF / Office extractor: IBM Docling.

Docling preserves layout, tables, and reading order far better than
lightweight text extractors. It's the default for text-bearing PDFs and
for DOCX / PPTX / XLSX when available. First run downloads ML models
(~1-2 GB cached under the user's HF cache dir).
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


class DoclingExtractor:
    """Docling-backed extractor. Works for PDF, DOCX, PPTX, XLSX, HTML."""

    name = "docling"

    def extract(self, path: Path) -> ExtractionResult:
        try:
            # Lazy import — lets the router skip us if docling isn't installed.
            from docling.document_converter import DocumentConverter
        except ImportError as exc:
            raise ExtractorUnavailable(
                "docling is not installed (pip install docling)"
            ) from exc

        start = time.perf_counter()
        try:
            converter = DocumentConverter()
            result = converter.convert(str(path))
        except Exception as exc:  # noqa: BLE001 - docling raises a wide variety
            raise ExtractorError(f"docling failed on {path.name}: {exc}") from exc

        # Docling returns a ConversionResult with a `.document` attribute that
        # has `.export_to_markdown()`. The exact shape has shifted across
        # versions, so defensively try both.
        doc = getattr(result, "document", None) or result
        try:
            markdown = doc.export_to_markdown()
        except AttributeError as exc:
            raise ExtractorError(
                f"docling produced an unexpected result shape: {type(result).__name__}"
            ) from exc

        duration_ms = int((time.perf_counter() - start) * 1000)
        page_count = _extract_page_count(doc)

        return ExtractionResult(
            markdown=markdown.strip() + "\n",
            engine=self.name,
            page_count=page_count,
            word_count=word_count(markdown),
            duration_ms=duration_ms,
            fallback_chain=[self.name],
            extra={"docling_version": _docling_version()},
        )


def _extract_page_count(doc) -> int | None:  # type: ignore[no-untyped-def]
    """Best-effort page count lookup across docling versions."""
    for attr in ("num_pages", "page_count", "pages"):
        value = getattr(doc, attr, None)
        if callable(value):
            try:
                value = value()
            except Exception:  # noqa: BLE001
                value = None
        if isinstance(value, int):
            return value
        if hasattr(value, "__len__"):
            try:
                return len(value)
            except TypeError:
                pass
    return None


def _docling_version() -> str:
    try:
        import docling  # type: ignore[import-not-found]
        return getattr(docling, "__version__", "unknown")
    except ImportError:
        return "unknown"

