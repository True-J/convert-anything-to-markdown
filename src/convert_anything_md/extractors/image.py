"""Image → Markdown via Tesseract OCR.

Supports PNG / JPG / TIFF / BMP / WEBP / GIF (Pillow handles format
decoding). The output is a single Markdown heading + OCR text block.

Requires the `tesseract` binary on PATH. If absent, raises
`ExtractorUnavailable` so the router can surface a helpful install hint.
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


class ImageOcrExtractor:
    """Tesseract-backed image → Markdown."""

    name = "tesseract"

    def extract(self, path: Path) -> ExtractionResult:
        if not shutil.which("tesseract"):
            raise ExtractorUnavailable(
                "tesseract binary missing. Install: "
                "macOS → `brew install tesseract`; "
                "Linux → `apt/dnf/pacman install tesseract-ocr`; "
                "Windows → https://github.com/UB-Mannheim/tesseract/wiki"
            )

        try:
            import pytesseract
            from PIL import Image
        except ImportError as exc:
            raise ExtractorUnavailable(
                "pytesseract + pillow are required for OCR"
            ) from exc

        start = time.perf_counter()
        try:
            with Image.open(path) as img:
                # Flatten palette / RGBA → RGB so Tesseract gets clean input.
                if img.mode not in ("RGB", "L"):
                    img = img.convert("RGB")
                text = pytesseract.image_to_string(img) or ""
        except Exception as exc:  # noqa: BLE001
            raise ExtractorError(f"OCR failed on {path.name}: {exc}") from exc

        text = text.strip()
        markdown = (
            f"# {path.stem}\n\n{text}\n"
            if text
            else f"# {path.stem}\n\n_(No text detected in image.)_\n"
        )
        duration_ms = int((time.perf_counter() - start) * 1000)
        return ExtractionResult(
            markdown=markdown,
            engine=self.name,
            word_count=word_count(text),
            duration_ms=duration_ms,
            fallback_chain=[self.name],
        )

