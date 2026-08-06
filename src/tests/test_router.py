"""Integration tests for the router.

These don't exercise heavy extractors like Docling — they use the pure-
Python fallbacks that are guaranteed to be installed (python-docx,
openpyxl, plaintext, markdown passthrough) and the `--engine` override to
force a deterministic path.
"""

from __future__ import annotations

from pathlib import Path

from convert_anything_md.detect import FileKind
from convert_anything_md.router import convert_batch, convert_file


def test_convert_plaintext_roundtrip(tmp_path: Path):
    src = tmp_path / "notes.txt"
    src.write_text("Hello world\nLine two\n")

    outcome = convert_file(
        src,
        output_dir=tmp_path / "out",
        engine_override="plaintext",
    )

    assert outcome.ok is True
    assert outcome.kind == FileKind.PLAINTEXT
    assert outcome.output is not None and outcome.output.exists()
    content = outcome.output.read_text(encoding="utf-8")
    assert content.startswith("---\n")  # front-matter on by default
    assert "Hello world" in content
    assert outcome.engine == "plaintext"


def test_convert_markdown_passthrough(tmp_path: Path):
    src = tmp_path / "doc.md"
    src.write_text("# Title\n\nBody paragraph.\n")

    outcome = convert_file(
        src,
        output_dir=tmp_path / "out",
        include_frontmatter=False,
    )

    assert outcome.ok is True
    assert outcome.output is not None
    content = outcome.output.read_text(encoding="utf-8")
    assert not content.startswith("---\n")  # frontmatter disabled
    assert "# Title" in content
    assert "Body paragraph." in content


def test_convert_conflict_safe_naming(tmp_path: Path):
    src = tmp_path / "same.txt"
    src.write_text("first")

    out_dir = tmp_path / "out"
    first = convert_file(src, output_dir=out_dir, engine_override="plaintext")
    second = convert_file(src, output_dir=out_dir, engine_override="plaintext")

    assert first.output == out_dir / "same.md"
    assert second.output == out_dir / "same (1).md"
    assert first.output.exists() and second.output.exists()


def test_convert_overwrite_flag(tmp_path: Path):
    src = tmp_path / "same.txt"
    src.write_text("first")
    out_dir = tmp_path / "out"
    out_dir.mkdir()
    (out_dir / "same.md").write_text("existing content")

    outcome = convert_file(
        src,
        output_dir=out_dir,
        engine_override="plaintext",
        overwrite=True,
    )

    assert outcome.output == out_dir / "same.md"
    # The original file content should be replaced.
    assert "existing content" not in outcome.output.read_text(encoding="utf-8")


def test_convert_dry_run_skips_write(tmp_path: Path):
    src = tmp_path / "note.txt"
    src.write_text("content")

    outcome = convert_file(
        src,
        output_dir=tmp_path / "out",
        dry_run=True,
    )

    assert outcome.ok is True
    assert outcome.output is not None
    assert not outcome.output.exists()


def test_convert_missing_file_returns_failed_outcome(tmp_path: Path):
    outcome = convert_file(tmp_path / "does-not-exist.pdf")
    assert outcome.ok is False
    assert "not found" in (outcome.error or "")


def test_convert_batch_handles_mixed_results(tmp_path: Path):
    good = tmp_path / "good.txt"
    good.write_text("readable")
    missing = tmp_path / "missing.pdf"  # deliberately not created

    outcomes = convert_batch([good, missing], output_dir=tmp_path / "out")
    assert len(outcomes) == 2
    assert outcomes[0].ok is True
    assert outcomes[1].ok is False

