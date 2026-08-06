"""AnyDoc (Firecrawl) extractor — Rust-powered office document conversion.

Shells out to the `anydoc` CLI (npm: @firecrawl/anydoc) which converts
Word, PowerPoint, Excel, OpenDocument, RTF, EPUB, CSV, and text-based PDFs
to GitHub-Flavored Markdown in single-digit milliseconds.

This is the **preferred first engine** for office documents because:
  - Pure Rust, no ML models, no external services
  - Unified Markdown serializer across all formats (consistent escaping,
    tables, heading anchors, footnotes)
  - 4.4ms median conversion time vs 100-500ms for Docling/MarkItDown
  - Supports OpenDocument formats (.odt/.ods/.odp) that no other extractor
    in the chain handles natively

Limitations (why it's not the ONLY engine):
  - No OCR for scanned PDFs or images
  - No HTML extraction
  - No plain-text/markdown passthrough
  - Scanned PDFs error as "unsupported" (caught and falls back gracefully)

The `anydoc` binary is installed via `npm install -g @firecrawl/anydoc`
or invoked ad-hoc via `npx @firecrawl/anydoc`. We check PATH first, then
fall back to npx with a download warning.
"""

from __future__ import annotations

import shutil
import subprocess
import time
from pathlib import Path

from convert_anything_md.extractors.base import (
    ExtractionResult,
    ExtractorError,
    ExtractorUnavailable,
    word_count,
)

# Cache the resolved binary path so we don't re-search PATH on every call.
_anydoc_bin: str | None = None
_anydoc_checked = False


def _find_anydoc() -> str | None:
    """Locate the anydoc binary. Returns the path or None."""
    global _anydoc_bin, _anydoc_checked
    if _anydoc_checked:
        return _anydoc_bin
    _anydoc_checked = True
    _anydoc_bin = shutil.which("anydoc")
    return _anydoc_bin


class AnyDocExtractor:
    """Office documents to Markdown via the anydoc Rust CLI.

    Handles: DOCX, DOC, PPTX, PPT, XLSX, XLS, ODT, ODS, ODP, RTF, EPUB, CSV,
    and text-based PDF. Does NOT handle scanned PDFs, images, or HTML.
    """

    name = "anydoc"

    def extract(self, path: Path) -> ExtractionResult:
        binary = _find_anydoc()
        if binary is None:
            raise ExtractorUnavailable(
                "anydoc CLI not found — install with: npm install -g @firecrawl/anydoc"
            )

        start = time.perf_counter()
        try:
            result = subprocess.run(
                [binary, str(path)],
                capture_output=True,
                text=True,
                timeout=30,
            )
        except subprocess.TimeoutExpired as exc:
            raise ExtractorError(f"anydoc timed out on {path.name} (30s)") from exc
        except FileNotFoundError as exc:
            raise ExtractorUnavailable(
                "anydoc CLI not found — install with: npm install -g @firecrawl/anydoc"
            ) from exc

        duration_ms = int((time.perf_counter() - start) * 1000)

        if result.returncode == 0:
            markdown = result.stdout
            return ExtractionResult(
                markdown=markdown,
                engine=self.name,
                word_count=word_count(markdown),
                duration_ms=duration_ms,
                fallback_chain=[self.name],
            )

        # Exit code 1 = conversion failed (corrupt file, unsupported sub-format,
        # scanned PDF, etc). Exit code 2 = usage error (shouldn't happen here).
        stderr = result.stderr.strip()
        if result.returncode == 1:
            raise ExtractorError(f"anydoc failed on {path.name}: {stderr}")
        # Unexpected exit code — treat as a crash.
        raise ExtractorError(
            f"anydoc exited with code {result.returncode} on {path.name}: {stderr}"
        )
