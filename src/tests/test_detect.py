"""Tests for file-type detection and the scanned-PDF heuristic."""

from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

from convert_anything_md.detect import FileKind, detect_kind, is_scanned_pdf

# ---------------------------------------------------------------------------
# Extension-driven detection (the fast path)
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "filename,expected",
    [
        ("doc.pdf", FileKind.PDF_TEXT),
        ("report.docx", FileKind.DOCX),
        ("slides.pptx", FileKind.PPTX),
        ("data.xlsx", FileKind.XLSX),
        ("rows.csv", FileKind.CSV),
        ("page.html", FileKind.HTML),
        ("book.epub", FileKind.EPUB),
        ("note.rtf", FileKind.RTF),
        ("readme.md", FileKind.MARKDOWN),
        ("notes.txt", FileKind.PLAINTEXT),
        ("image.png", FileKind.IMAGE),
        ("photo.JPG", FileKind.IMAGE),  # case-insensitive
        ("scan.TIFF", FileKind.IMAGE),
    ],
)
def test_detect_kind_by_extension(tmp_path: Path, filename: str, expected: FileKind):
    path = tmp_path / filename
    path.write_bytes(b"dummy")
    assert detect_kind(path) == expected


def test_detect_kind_returns_unknown_for_missing_file(tmp_path: Path):
    assert detect_kind(tmp_path / "nope.xyz") == FileKind.UNKNOWN


# ---------------------------------------------------------------------------
# Magic-byte sniffing (extensionless / mis-named files)
# ---------------------------------------------------------------------------


def test_detect_pdf_by_magic_no_extension(tmp_path: Path):
    path = tmp_path / "mystery"
    path.write_bytes(b"%PDF-1.7\n%..." + b"\x00" * 100)
    assert detect_kind(path) == FileKind.PDF_TEXT


def test_detect_png_by_magic(tmp_path: Path):
    path = tmp_path / "thumb"
    path.write_bytes(b"\x89PNG\r\n\x1a\n" + b"\x00" * 50)
    assert detect_kind(path) == FileKind.IMAGE


def test_detect_jpeg_by_magic(tmp_path: Path):
    path = tmp_path / "pic"
    path.write_bytes(b"\xff\xd8\xff\xe0" + b"\x00" * 50)
    assert detect_kind(path) == FileKind.IMAGE


def test_detect_html_by_magic(tmp_path: Path):
    path = tmp_path / "page"
    path.write_bytes(b"<html><body>hi</body></html>")
    assert detect_kind(path) == FileKind.HTML


def test_detect_plaintext_by_content(tmp_path: Path):
    path = tmp_path / "notes"
    path.write_bytes(b"just some plain text content\nwith a newline\n")
    assert detect_kind(path) == FileKind.PLAINTEXT


# ---------------------------------------------------------------------------
# OOXML container disambiguation
# ---------------------------------------------------------------------------


def test_detect_docx_via_ooxml_zip(tmp_path: Path):
    import zipfile

    path = tmp_path / "no-extension-here"
    with zipfile.ZipFile(path, "w") as zf:
        zf.writestr("word/document.xml", "<w:document/>")
        zf.writestr("[Content_Types].xml", "<Types/>")
    assert detect_kind(path) == FileKind.DOCX


def test_detect_xlsx_via_ooxml_zip(tmp_path: Path):
    import zipfile

    path = tmp_path / "book"
    with zipfile.ZipFile(path, "w") as zf:
        zf.writestr("xl/workbook.xml", "<xl/>")
        zf.writestr("[Content_Types].xml", "<Types/>")
    assert detect_kind(path) == FileKind.XLSX


def test_detect_pptx_via_ooxml_zip(tmp_path: Path):
    import zipfile

    path = tmp_path / "deck"
    with zipfile.ZipFile(path, "w") as zf:
        zf.writestr("ppt/presentation.xml", "<p/>")
        zf.writestr("[Content_Types].xml", "<Types/>")
    assert detect_kind(path) == FileKind.PPTX


# ---------------------------------------------------------------------------
# Scanned-PDF heuristic
# ---------------------------------------------------------------------------
#
# These tests need PyMuPDF (`fitz`) at runtime. Earlier revisions placed
# `pytest.importorskip("fitz")` at module scope, which skipped the entire
# file when PyMuPDF was missing - including all the extension/magic-byte
# tests above, which do not need fitz. Now each PDF test opts in via a
# function-level decorator, so the rest of the module always runs.

_HAS_FITZ = importlib.util.find_spec("fitz") is not None
requires_fitz = pytest.mark.skipif(
    not _HAS_FITZ, reason="PyMuPDF (fitz) is required for scanned-PDF tests"
)


def _make_text_pdf(path: Path, pages: int = 3, words_per_page: int = 300) -> None:
    """Build a PDF with embedded text using PyMuPDF.

    Uses insert_textbox so the text actually wraps across lines instead
    of being clipped after the first line (which is what insert_text
    does). This guarantees enough extractable characters per page to
    clear the scanned-vs-text threshold.
    """
    import fitz  # noqa: PLC0415 - lazy import so module loads without fitz

    doc = fitz.open()
    text_block = " ".join(["lorem"] * words_per_page)
    for _ in range(pages):
        page = doc.new_page()
        # Full-page text box with generous margins.
        rect = fitz.Rect(50, 50, page.rect.width - 50, page.rect.height - 50)
        page.insert_textbox(rect, text_block, fontsize=10)
    doc.save(str(path))
    doc.close()


def _make_blank_pdf(path: Path, pages: int = 3) -> None:
    """Build a PDF with no embedded text - simulates a scanned doc."""
    import fitz  # noqa: PLC0415

    doc = fitz.open()
    for _ in range(pages):
        doc.new_page()
    doc.save(str(path))
    doc.close()


@requires_fitz
def test_is_scanned_pdf_false_for_text_pdf(tmp_path: Path):
    path = tmp_path / "text.pdf"
    _make_text_pdf(path)
    assert is_scanned_pdf(path) is False


@requires_fitz
def test_is_scanned_pdf_true_for_blank_pdf(tmp_path: Path):
    path = tmp_path / "blank.pdf"
    _make_blank_pdf(path)
    assert is_scanned_pdf(path) is True


def test_is_scanned_pdf_returns_false_on_missing_file(tmp_path: Path):
    # This one does NOT need fitz - the missing-file branch returns before
    # opening any PDF.
    assert is_scanned_pdf(tmp_path / "does-not-exist.pdf") is False
