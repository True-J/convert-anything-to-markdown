"""Tests for the CLI's input resolution + flag handling.

These tests guard against the 1.3.x regressions that:
* lost the subdir component of a relative glob (`docs/*.pdf` searched CWD,
  not `./docs/`);
* silently dropped a directory argument with exit code 2 and no error;
* silently accepted `--engine X` for a file kind whose chain didn't include
  X, with no warning surfaced to the user.
"""

from __future__ import annotations

import io
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

from convert_anything_md.cli import _resolve_inputs, main
from convert_anything_md.extractors.text import PlainTextExtractor
from convert_anything_md.router import EXTRACTOR_NAMES, _reorder_for_override

# ---------------------------------------------------------------------------
# _resolve_inputs: literal files, missing files, dedup
# ---------------------------------------------------------------------------


def test_resolve_inputs_returns_existing_files(tmp_path: Path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "a.txt").write_text("hi")
    (tmp_path / "b.txt").write_text("hi")

    resolved, missing, dirs = _resolve_inputs(["a.txt", "b.txt"])
    assert {p.name for p in resolved} == {"a.txt", "b.txt"}
    assert missing == []
    assert dirs == []


def test_resolve_inputs_reports_missing(tmp_path: Path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    resolved, missing, dirs = _resolve_inputs(["does-not-exist.pdf"])
    assert resolved == []
    assert missing == ["does-not-exist.pdf"]
    assert dirs == []


def test_resolve_inputs_dedup_collapses_duplicates(tmp_path: Path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "one.txt").write_text("hi")
    resolved, _, _ = _resolve_inputs(["one.txt", "./one.txt", str(tmp_path / "one.txt")])
    assert len(resolved) == 1


# ---------------------------------------------------------------------------
# Glob expansion: the relative-subdir bug
# ---------------------------------------------------------------------------


def test_resolve_inputs_glob_relative_with_subdir(tmp_path: Path, monkeypatch):
    """Regression: `docs/*.pdf` from CWD must find files inside docs/, not in CWD.

    Pre-1.4.0 the CLI stripped the directory component off the glob,
    so `docs/*.pdf` was effectively `*.pdf` against CWD. This test
    enforces the corrected behavior.
    """
    monkeypatch.chdir(tmp_path)
    docs = tmp_path / "docs"
    docs.mkdir()
    (docs / "a.pdf").write_bytes(b"%PDF-")
    (docs / "b.pdf").write_bytes(b"%PDF-")
    # Decoy file in CWD - if the old behavior leaks back, this would be
    # the only match.
    (tmp_path / "decoy.pdf").write_bytes(b"%PDF-")

    resolved, _, _ = _resolve_inputs(["docs/*.pdf"])
    names = sorted(p.name for p in resolved)
    assert names == ["a.pdf", "b.pdf"]
    assert all("decoy" not in p.name for p in resolved)


def test_resolve_inputs_glob_absolute(tmp_path: Path):
    (tmp_path / "alpha.txt").write_text("hi")
    (tmp_path / "beta.txt").write_text("hi")
    resolved, _, _ = _resolve_inputs([str(tmp_path / "*.txt")])
    assert {p.name for p in resolved} == {"alpha.txt", "beta.txt"}


def test_resolve_inputs_glob_no_matches_reports_missing(tmp_path: Path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    resolved, missing, dirs = _resolve_inputs(["*.pdf"])
    assert resolved == []
    assert missing == ["*.pdf"]
    assert dirs == []


# ---------------------------------------------------------------------------
# Directory handling: silent-drop regression
# ---------------------------------------------------------------------------


def test_resolve_inputs_directory_without_recursive(tmp_path: Path):
    docs = tmp_path / "docs"
    docs.mkdir()
    (docs / "a.txt").write_text("hi")

    resolved, missing, dirs = _resolve_inputs([str(docs)], recursive=False)
    assert resolved == []
    assert missing == []
    assert dirs == [docs.resolve()]


def test_resolve_inputs_directory_with_recursive(tmp_path: Path):
    docs = tmp_path / "docs"
    docs.mkdir()
    (docs / "a.txt").write_text("hi")
    (docs / "b.md").write_text("# hi")
    (docs / ".secret").write_text("hidden file")
    (docs / "junk.xyz").write_text("unknown kind")

    nested = docs / "nested"
    nested.mkdir()
    (nested / "c.csv").write_text("a,b\n1,2\n")

    resolved, missing, dirs = _resolve_inputs([str(docs)], recursive=True)
    names = sorted(p.name for p in resolved)
    # Dotfile excluded, unknown extension excluded; rest included.
    assert names == ["a.txt", "b.md", "c.csv"]
    assert missing == []
    assert dirs == []


def test_resolve_inputs_skips_known_build_dirs(tmp_path: Path):
    docs = tmp_path / "project"
    docs.mkdir()
    (docs / "real.md").write_text("# real")

    git_dir = docs / ".git" / "objects"
    git_dir.mkdir(parents=True)
    (git_dir / "ignored.md").write_text("# secret")

    venv_dir = docs / ".venv" / "site-packages"
    venv_dir.mkdir(parents=True)
    (venv_dir / "skipped.md").write_text("# venv")

    resolved, _, _ = _resolve_inputs([str(docs)], recursive=True)
    names = sorted(p.name for p in resolved)
    assert names == ["real.md"]


# ---------------------------------------------------------------------------
# CLI integration: directory input emits an error message + exit code
# ---------------------------------------------------------------------------


def test_main_directory_input_emits_error(tmp_path: Path):
    """Regression: passing a directory used to exit 2 silently."""
    (tmp_path / "child.txt").write_text("hi")

    stderr = io.StringIO()
    stdout = io.StringIO()
    with redirect_stderr(stderr), redirect_stdout(stdout):
        rc = main([str(tmp_path), "--dry-run"])
    assert rc == 2
    assert "is a directory" in stderr.getvalue()
    assert "--recursive" in stderr.getvalue()


def test_main_directory_with_recursive_succeeds(tmp_path: Path):
    src_dir = tmp_path / "src"
    src_dir.mkdir()
    (src_dir / "note.txt").write_text("hello world")
    out_dir = tmp_path / "out"

    stdout = io.StringIO()
    with redirect_stdout(stdout):
        rc = main([
            str(src_dir),
            "--recursive",
            "--json",
            "-o",
            str(out_dir),
        ])
    assert rc == 0
    # One .md file should be produced.
    md_files = list(out_dir.glob("*.md"))
    assert len(md_files) == 1


def test_main_list_engines(capsys):
    rc = main(["--list-engines"])
    captured = capsys.readouterr()
    assert rc == 0
    # Every name advertised by EXTRACTOR_NAMES should be listed.
    for name in EXTRACTOR_NAMES:
        assert name in captured.out


def test_main_quiet_suppresses_table(tmp_path: Path, capsys):
    src = tmp_path / "note.txt"
    src.write_text("hello")
    out_dir = tmp_path / "out"

    rc = main(["--quiet", "-o", str(out_dir), str(src)])
    captured = capsys.readouterr()
    assert rc == 0
    assert "convert-anything-md" not in captured.out  # no table title
    # but the .md should still be on disk
    assert any(out_dir.glob("*.md"))


# ---------------------------------------------------------------------------
# Engine override: silent fall-through regression
# ---------------------------------------------------------------------------


def test_reorder_for_override_warns_when_engine_not_in_chain():
    chain = [PlainTextExtractor]
    reordered, warnings = _reorder_for_override(chain, "docling")
    assert reordered == chain
    assert len(warnings) == 1
    assert "docling" in warnings[0]
    assert "plaintext" in warnings[0]


def test_reorder_for_override_no_warning_when_engine_matches():
    chain = [PlainTextExtractor]
    reordered, warnings = _reorder_for_override(chain, "plaintext")
    assert reordered == chain
    assert warnings == []


def test_reorder_for_override_no_warning_when_no_override():
    chain = [PlainTextExtractor]
    reordered, warnings = _reorder_for_override(chain, None)
    assert reordered == chain
    assert warnings == []


def test_reorder_for_override_does_not_instantiate_classes():
    """Regression: `cls().name` used to instantiate just to read .name."""

    class CountingExtractor:
        name = "counting"
        instance_count = 0

        def __init__(self):
            CountingExtractor.instance_count += 1

        def extract(self, path):  # pragma: no cover - never invoked
            raise NotImplementedError

    chain = [CountingExtractor, PlainTextExtractor]
    _reorder_for_override(chain, "plaintext")
    assert CountingExtractor.instance_count == 0


# ---------------------------------------------------------------------------
# Engine override end-to-end: warning propagates into outcome.warnings
# ---------------------------------------------------------------------------


def test_engine_override_warning_visible_in_outcome(tmp_path: Path):
    """Engine that doesn't apply to a kind should produce a visible warning."""
    from convert_anything_md.router import convert_file

    src = tmp_path / "note.txt"
    src.write_text("hi there")

    outcome = convert_file(
        src,
        output_dir=tmp_path / "out",
        engine_override="docling",  # plaintext chain only has PlainTextExtractor
    )
    assert outcome.ok is True
    # The warning is now surfaced rather than silently swallowed.
    assert any("docling" in w for w in outcome.warnings)
