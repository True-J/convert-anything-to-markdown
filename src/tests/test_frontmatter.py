"""Tests for the YAML front-matter builder."""

from __future__ import annotations

from pathlib import Path

import yaml

from convert_anything_md.frontmatter import build_frontmatter


def test_build_frontmatter_produces_valid_yaml(tmp_path: Path):
    src = tmp_path / "report.pdf"
    src.write_bytes(b"%PDF-1.4 fake content")

    block = build_frontmatter(
        source=src,
        engine="docling",
        fallback_chain=["docling"],
        pages=42,
        word_count=9_847,
        duration_ms=3_200,
    )

    assert block.startswith("---\n")
    assert block.endswith("---\n\n")

    # Strip fences and round-trip through yaml.
    yaml_body = block.split("---\n", 2)[1]
    parsed = yaml.safe_load(yaml_body)
    assert parsed["engine"] == "docling"
    assert parsed["pages"] == 42
    assert parsed["word_count"] == 9_847
    assert parsed["duration_ms"] == 3_200
    assert parsed["source"] == str(src.resolve())
    assert parsed["source_name"] == "report.pdf"
    assert parsed["fallback_chain"] == ["docling"]
    assert parsed["warnings"] == []
    assert len(parsed["source_sha256"]) == 64  # sha256 hex length
    assert parsed["converter"].startswith("convert-anything-md@")
    assert "source_sha256_error" not in parsed


def test_build_frontmatter_drops_none_fields(tmp_path: Path):
    src = tmp_path / "note.txt"
    src.write_text("hi")

    block = build_frontmatter(
        source=src,
        engine="plaintext",
        pages=None,
        word_count=1,
        duration_ms=1,
    )
    yaml_body = block.split("---\n", 2)[1]
    parsed = yaml.safe_load(yaml_body)
    assert "pages" not in parsed  # None pages must be dropped


def test_build_frontmatter_merges_extra(tmp_path: Path):
    src = tmp_path / "sheet.xlsx"
    src.write_bytes(b"")
    block = build_frontmatter(
        source=src,
        engine="openpyxl",
        word_count=100,
        duration_ms=50,
        extra={"sheet_count": 3},
    )
    parsed = yaml.safe_load(block.split("---\n", 2)[1])
    assert parsed["sheet_count"] == 3


def test_build_frontmatter_surfaces_warnings(tmp_path: Path):
    src = tmp_path / "scan.pdf"
    src.write_bytes(b"%PDF-")
    block = build_frontmatter(
        source=src,
        engine="pdf_ocr",
        word_count=0,
        duration_ms=5_000,
        warnings=["docling unavailable", "page 3: OCR noisy"],
    )
    parsed = yaml.safe_load(block.split("---\n", 2)[1])
    assert parsed["warnings"] == ["docling unavailable", "page 3: OCR noisy"]


def test_build_frontmatter_surfaces_hash_error_when_file_unreadable(
    tmp_path: Path,
):
    """A failed SHA-256 used to be a silent empty string in the YAML.

    The kit's front-matter is a provenance contract for downstream tools;
    a blank SHA could mislead verifiers. Now we emit an explicit
    `source_sha256_error` field whenever hashing fails.
    """
    src = tmp_path / "nonexistent.pdf"
    # Intentionally do NOT create the file - the hash open() will raise OSError.

    block = build_frontmatter(
        source=src,
        engine="docling",
        word_count=0,
        duration_ms=10,
    )
    parsed = yaml.safe_load(block.split("---\n", 2)[1])
    assert parsed["source_sha256"] == ""
    assert "source_sha256_error" in parsed
    assert parsed["source_sha256_error"]  # non-empty error description
