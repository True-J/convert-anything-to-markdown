"""Extractor protocol, result type, and shared exceptions.

Every concrete extractor (`pdf_docling`, `pdf_ocr`, `office`, `html`,
`epub`, `text`, `image`) implements `Extractor`. The router wires primary
+ fallback chains out of these and invokes `.extract()`.

Key design decisions:

* **ExtractorUnavailable** is raised when the backing library or external
  binary isn't installed — the router treats this as "try the next
  extractor" rather than a real failure.
* **ExtractorError** is raised when the extractor ran but failed (corrupt
  file, unsupported sub-format, etc.) — the router still falls back, but
  surfaces the message as a warning in the final result.
* **ExtractionResult** is immutable (a frozen dataclass). Callers build a
  fresh result and the router mutates a copy via `dataclasses.replace`.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Protocol, runtime_checkable


@dataclass(frozen=True)
class ExtractionResult:
    """Output of a single extraction attempt.

    Attributes:
        markdown:        The extracted Markdown body (no front-matter).
        engine:          Name of the tool that produced this result
                         (e.g. ``"docling"``, ``"markitdown"``,
                         ``"pdftotext+tesseract"``).
        page_count:      Number of pages (PDF, PPTX) or None if N/A.
        word_count:      Rough word count of the extracted Markdown.
        duration_ms:     Wall-clock extraction time in milliseconds.
        warnings:        Non-fatal messages (e.g. "fell back from docling").
        fallback_chain:  Ordered list of engines actually attempted.
        extra:           Extractor-specific metadata (surfaced in
                         front-matter).
    """

    markdown: str
    engine: str
    page_count: int | None = None
    word_count: int = 0
    duration_ms: int = 0
    warnings: list[str] = field(default_factory=list)
    fallback_chain: list[str] = field(default_factory=list)
    extra: dict = field(default_factory=dict)


class ExtractorError(RuntimeError):
    """The extractor ran but could not complete (bad input, etc.)."""


class ExtractorUnavailable(ExtractorError):
    """The backing library or binary isn't installed on this system."""


@runtime_checkable
class Extractor(Protocol):
    """Common interface for every document extractor."""

    name: str  # Short identifier that appears in front-matter.

    def extract(self, path: Path) -> ExtractionResult:
        """Read `path` and return an `ExtractionResult`.

        Raises:
            ExtractorUnavailable: backing tool isn't installed.
            ExtractorError:       tool is installed but extraction failed.
        """
        ...


def word_count(text: str) -> int:
    """Fast whitespace-split word count. Good enough for provenance stats."""
    return len(text.split()) if text else 0

