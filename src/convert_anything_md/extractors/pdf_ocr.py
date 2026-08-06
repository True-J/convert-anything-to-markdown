"""OCR path for scanned PDFs.

Strategy:

1. If the `tesseract` binary is on PATH, rasterize pages with PyMuPDF
   (pure Python, no poppler required → works on Windows out of the box)
   and feed each page image to Tesseract via `pytesseract`. Stitch the
   results into Markdown with a `## Page N` header per page.
2. If `tesseract` isn't installed, raise `ExtractorUnavailable` so the
   router can surface a helpful message to the user.

We use PyMuPDF (a.k.a. `fitz`) for rasterization instead of
`pdf2image`/`poppler` because PyMuPDF ships as a pure wheel on all OSes
and doesn't require a separate system dependency.
"""

from __future__ import annotations

import shutil
import time
from pathlib import Path

from convert_anything_md.extractors.base import (
    ExtractionResult,
    ExtractorError,
    ExtractorUnavailable,
    word_count,
)


class PdfOcrExtractor:
    """Rasterize + Tesseract OCR for scanned PDFs."""

    name = "pdf_ocr"

    # Rasterization DPI — 300 is the sweet spot for OCR accuracy without
    # blowing up memory on long PDFs.
    dpi: int = 300

    def extract(self, path: Path) -> ExtractionResult:
        try:
            import fitz  # pymupdf
        except ImportError as exc:
            raise ExtractorUnavailable(
                "pymupdf is not installed (pip install pymupdf)"
            ) from exc

        try:
            import pytesseract
            from PIL import Image
        except ImportError as exc:
            raise ExtractorUnavailable(
                "pytesseract + pillow are not installed "
                "(pip install pytesseract pillow)"
            ) from exc

        if not shutil.which("tesseract"):
            raise ExtractorUnavailable(
                "the tesseract binary is not on PATH. Install it via: "
                "macOS → `brew install tesseract`; "
                "Linux → `apt/dnf/pacman install tesseract-ocr`; "
                "Windows → https://github.com/UB-Mannheim/tesseract/wiki"
            )

        start = time.perf_counter()
        zoom = self.dpi / 72.0  # PyMuPDF default DPI is 72.

        try:
            doc = fitz.open(str(path))
        except Exception as exc:  # noqa: BLE001
            raise ExtractorError(f"could not open {path.name}: {exc}") from exc

        page_count = 0
        page_markdowns: list[str] = []
        warnings: list[str] = []

        try:
            page_count = doc.page_count
            matrix = fitz.Matrix(zoom, zoom)
            for idx in range(page_count):
                try:
                    page = doc.load_page(idx)
                    pixmap = page.get_pixmap(matrix=matrix, alpha=False)
                    image = Image.frombytes(
                        "RGB", (pixmap.width, pixmap.height), pixmap.samples
                    )
                    text = pytesseract.image_to_string(image) or ""
                except Exception as exc:  # noqa: BLE001
                    warnings.append(f"page {idx + 1}: OCR failed ({exc})")
                    text = ""

                text = text.strip()
                if text:
                    page_markdowns.append(f"## Page {idx + 1}\n\n{text}")
        finally:
            doc.close()

        if not page_markdowns:
            raise ExtractorError(
                f"OCR produced no text for {path.name} — the PDF may be "
                "encrypted or contain only blank/diagram pages."
            )

        markdown = "\n\n".join(page_markdowns) + "\n"
        duration_ms = int((time.perf_counter() - start) * 1000)

        return ExtractionResult(
            markdown=markdown,
            engine=self.name,
            page_count=page_count,
            word_count=word_count(markdown),
            duration_ms=duration_ms,
            warnings=warnings,
            fallback_chain=[self.name],
            extra={"ocr_dpi": self.dpi},
        )

