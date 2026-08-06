"""Tests for cross-platform path resolution and conflict-safe naming."""

from __future__ import annotations

import os
from pathlib import Path
from unittest.mock import patch

import pytest

from convert_anything_md.paths import (
    conflict_safe_name,
    desktop_dir,
    ensure_dir,
    safe_stem,
)


# ---------------------------------------------------------------------------
# conflict_safe_name
# ---------------------------------------------------------------------------


def test_conflict_safe_name_returns_stem_when_dir_empty(tmp_path: Path):
    result = conflict_safe_name(tmp_path, "report")
    assert result == tmp_path / "report.md"


def test_conflict_safe_name_increments_on_collision(tmp_path: Path):
    (tmp_path / "report.md").write_text("")
    result = conflict_safe_name(tmp_path, "report")
    assert result == tmp_path / "report (1).md"


def test_conflict_safe_name_keeps_incrementing(tmp_path: Path):
    (tmp_path / "report.md").write_text("")
    (tmp_path / "report (1).md").write_text("")
    (tmp_path / "report (2).md").write_text("")
    result = conflict_safe_name(tmp_path, "report")
    assert result == tmp_path / "report (3).md"


def test_conflict_safe_name_strips_existing_counter_suffix(tmp_path: Path):
    # Re-running with "report (1)" as input should NOT produce "report (1) (1).md"
    (tmp_path / "report.md").write_text("")
    result = conflict_safe_name(tmp_path, "report (1)")
    assert result == tmp_path / "report (1).md"


def test_conflict_safe_name_custom_extension(tmp_path: Path):
    (tmp_path / "data.json").write_text("")
    result = conflict_safe_name(tmp_path, "data", ".json")
    assert result == tmp_path / "data (1).json"


def test_conflict_safe_name_adds_dot_when_missing(tmp_path: Path):
    result = conflict_safe_name(tmp_path, "note", "txt")
    assert result == tmp_path / "note.txt"


def test_conflict_safe_name_empty_extension(tmp_path: Path):
    result = conflict_safe_name(tmp_path, "LICENSE", "")
    assert result == tmp_path / "LICENSE"


# ---------------------------------------------------------------------------
# safe_stem
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "input_name,expected",
    [
        ("normal_file.pdf", "normal_file"),
        ('bad:name<with>"quotes".pdf', "bad_name_with__quotes_"),
        ("trailing dots....pdf", "trailing dots"),
        ("  whitespace  mess .pdf", "whitespace mess"),
        ("", "converted"),
        (".bashrc", "bashrc"),          # dot-file → leading dot stripped
        (".pdf", "pdf"),                # dot-file with ext-looking name
        ("...", "converted"),           # pure dots → fallback
        ("   ", "converted"),           # pure whitespace → fallback
    ],
)
def test_safe_stem_normalizes_bad_characters(input_name: str, expected: str):
    assert safe_stem(Path(input_name)) == expected


def test_safe_stem_truncates_long_names():
    long_name = "a" * 500 + ".pdf"
    result = safe_stem(Path(long_name))
    assert len(result) <= 200


# ---------------------------------------------------------------------------
# desktop_dir (cross-platform)
# ---------------------------------------------------------------------------


def test_desktop_dir_returns_path():
    result = desktop_dir()
    assert isinstance(result, Path)
    # Must be absolute on every OS we support.
    assert result.is_absolute() or result == Path.cwd()


def test_desktop_dir_macos(tmp_path: Path, monkeypatch):
    fake_home = tmp_path / "home"
    (fake_home / "Desktop").mkdir(parents=True)
    monkeypatch.setattr("convert_anything_md.paths.Path.home", lambda: fake_home)
    monkeypatch.setattr("sys.platform", "darwin")
    result = desktop_dir()
    assert result == fake_home / "Desktop"


def test_desktop_dir_linux_with_xdg_user_dirs(tmp_path: Path, monkeypatch):
    fake_home = tmp_path / "home"
    fake_home.mkdir()
    (fake_home / "MyDesktop").mkdir()

    xdg_config = fake_home / ".config"
    xdg_config.mkdir()
    (xdg_config / "user-dirs.dirs").write_text(
        'XDG_DESKTOP_DIR="$HOME/MyDesktop"\n'
    )

    monkeypatch.setattr("convert_anything_md.paths.Path.home", lambda: fake_home)
    monkeypatch.setattr("sys.platform", "linux")
    monkeypatch.setenv("XDG_CONFIG_HOME", str(xdg_config))

    result = desktop_dir()
    assert result == fake_home / "MyDesktop"


def test_desktop_dir_linux_without_xdg_falls_back(tmp_path: Path, monkeypatch):
    fake_home = tmp_path / "home"
    fake_home.mkdir()
    (fake_home / "Desktop").mkdir()

    monkeypatch.setattr("convert_anything_md.paths.Path.home", lambda: fake_home)
    monkeypatch.setattr("sys.platform", "linux")
    monkeypatch.delenv("XDG_CONFIG_HOME", raising=False)

    result = desktop_dir()
    assert result == fake_home / "Desktop"


# ---------------------------------------------------------------------------
# ensure_dir
# ---------------------------------------------------------------------------


def test_ensure_dir_creates_missing(tmp_path: Path):
    target = tmp_path / "a" / "b" / "c"
    assert not target.exists()
    result = ensure_dir(target)
    assert result.is_dir()
    assert result == target


def test_ensure_dir_tolerates_existing(tmp_path: Path):
    ensure_dir(tmp_path)  # must not raise

