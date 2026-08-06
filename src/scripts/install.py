#!/usr/bin/env python3
"""Cross-platform installer for convert-anything-md.

Detects `uv`, falls back to `pipx`, then `pip --user`. Works on macOS,
Linux, and Windows without modification. Intended to be runnable with a
stock `python3` interpreter (no third-party dependencies).

Usage:
    python3 scripts/install.py
    python3 scripts/install.py --editable   # install this source tree
"""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from pathlib import Path

#: The Python package source tree (containing pyproject.toml) lives one
#: directory above scripts/, i.e. <kit>/src/. install.py lives at
#: <kit>/src/scripts/install.py, so .parent.parent IS the source tree.
#: Earlier releases (<= 1.3.6) appended an extra "/ src" segment which
#: resolved to a nonexistent path and broke every installer fallback.
BUNDLED_SRC = Path(__file__).resolve().parent.parent


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--editable",
        action="store_true",
        help="Install in editable (--editable) mode instead of a copy.",
    )
    parser.add_argument(
        "--index-url",
        help="Override the Python package index (for private mirrors).",
    )
    args = parser.parse_args()

    if not (BUNDLED_SRC / "pyproject.toml").is_file():
        print(
            f"ERROR: expected pyproject.toml at {BUNDLED_SRC}, but the file "
            "is missing. The kit bundle is incomplete - re-download it.",
            file=sys.stderr,
        )
        return 1

    target = str(BUNDLED_SRC)

    last_err: str | None = None
    for installer, cmd in _installer_candidates(args):
        print(f"-> Trying {installer}")
        rc = _run(cmd + [target])
        if rc == 0:
            print(f"\nOK Installed via {installer}")
            return _verify()
        last_err = f"{installer} exit code {rc}"
        print(f"  {installer} failed (exit {rc}); trying next option.\n")

    print(f"\nERROR: every installer failed. Last error: {last_err}", file=sys.stderr)
    print("Install Python 3.10+ and uv, then re-run. uv install docs:", file=sys.stderr)
    print("  https://docs.astral.sh/uv/getting-started/installation/", file=sys.stderr)
    return 1


def _installer_candidates(args) -> list[tuple[str, list[str]]]:  # noqa: ANN001
    index_args = ["--index-url", args.index_url] if args.index_url else []
    editable_flag = ["--editable"] if args.editable else []

    options: list[tuple[str, list[str]]] = []

    if shutil.which("uv"):
        options.append((
            "uv tool install",
            ["uv", "tool", "install", *editable_flag, *index_args],
        ))
    if shutil.which("pipx"):
        options.append((
            "pipx install",
            ["pipx", "install", *editable_flag, *index_args],
        ))
    # pip is virtually always present with Python.
    options.append((
        "pip install --user",
        [sys.executable, "-m", "pip", "install", "--user", *editable_flag, *index_args],
    ))
    return options


def _run(cmd: list[str]) -> int:
    try:
        return subprocess.run(cmd, check=False).returncode
    except FileNotFoundError as exc:
        print(f"  [skip] {exc}")
        return 127


def _verify() -> int:
    # `uv tool install` puts binaries under ~/.local/bin (Linux/macOS) or
    # %USERPROFILE%\.local\bin (Windows). Those may not be on PATH yet.
    exe = shutil.which("convert-anything-md")
    if not exe:
        print(
            "\nInstalled - but `convert-anything-md` isn't on PATH yet.\n"
            "Add the user bin directory to PATH and restart your terminal:\n"
            "  Linux/macOS: add $HOME/.local/bin to PATH in your shell rc\n"
            "  Windows:     add %USERPROFILE%\\.local\\bin to your user PATH\n"
            "Docs: https://docs.astral.sh/uv/concepts/tools/#the-path"
        )
        return 0
    print(f"\n{exe} is ready to use. Try:\n  convert-anything-md --version")
    return 0


if __name__ == "__main__":
    sys.exit(main())
