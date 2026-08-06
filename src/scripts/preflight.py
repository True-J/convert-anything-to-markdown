#!/usr/bin/env python3
"""Preflight check — reports which extractors are currently usable.

Run this any time to see what will happen on your machine:

    python3 scripts/preflight.py

The output helps diagnose "why is it falling back to X?" moments and
flags missing system tools with install hints tailored to the OS.

Works with a stock `python3` — no third-party dependencies required.
"""

from __future__ import annotations

import importlib
import shutil
import sys
from dataclasses import dataclass


@dataclass
class CheckResult:
    label: str
    ok: bool
    detail: str


def main() -> int:
    print(f"convert-anything-md preflight ({sys.platform})\n")

    rows: list[CheckResult] = []

    # Python runtime
    rows.append(
        CheckResult(
            "Python >= 3.10",
            sys.version_info >= (3, 10),
            f"{sys.version.split()[0]}",
        )
    )

    # Python packages
    for pkg, friendly in [
        ("fitz", "pymupdf"),
        ("docling", "docling"),
        ("markitdown", "markitdown"),
        ("trafilatura", "trafilatura"),
        ("ebooklib", "ebooklib"),
        ("docx", "python-docx"),
        ("pptx", "python-pptx"),
        ("openpyxl", "openpyxl"),
        ("bs4", "beautifulsoup4"),
        ("striprtf", "striprtf"),
        ("pytesseract", "pytesseract"),
        ("PIL", "pillow"),
        ("yaml", "pyyaml"),
        ("rich", "rich"),
    ]:
        try:
            importlib.import_module(pkg)
            rows.append(CheckResult(f"pypi/{friendly}", True, "installed"))
        except ImportError as exc:
            rows.append(
                CheckResult(f"pypi/{friendly}", False, f"not installed: {exc}")
            )

    # System binaries
    for binary, hint in [
        ("tesseract", _tesseract_hint()),
        ("pandoc", _pandoc_hint()),
        ("uv", "https://astral.sh/uv/"),
        ("pipx", "https://pipx.pypa.io/"),
    ]:
        path = shutil.which(binary)
        rows.append(
            CheckResult(
                f"bin/{binary}",
                path is not None,
                path or f"missing — {hint}",
            )
        )

    # CLI itself
    cli = shutil.which("convert-anything-md")
    rows.append(
        CheckResult(
            "cli/convert-anything-md",
            cli is not None,
            cli or "not installed; run: uv tool install ./src",
        )
    )

    _print_table(rows)

    # Summary + exit code
    required_failures = [r for r in rows if not r.ok and r.label == "Python >= 3.10"]
    if required_failures:
        print("\nX Required prerequisite missing.")
        return 1

    print("\nOptional tools that are missing only reduce quality for specific formats.")
    print("You can still install and use convert-anything-md.")
    return 0


def _tesseract_hint() -> str:
    if sys.platform == "darwin":
        return "brew install tesseract"
    if sys.platform == "win32":
        return "https://github.com/UB-Mannheim/tesseract/wiki"
    return "apt / dnf / pacman install tesseract-ocr"


def _pandoc_hint() -> str:
    if sys.platform == "darwin":
        return "brew install pandoc"
    if sys.platform == "win32":
        return "https://pandoc.org/installing.html"
    return "apt / dnf / pacman install pandoc"


def _print_table(rows: list[CheckResult]) -> None:
    width = max(len(r.label) for r in rows) + 2
    for r in rows:
        mark = "OK  " if r.ok else "--  "
        print(f"{mark}{r.label:<{width}}{r.detail}")


if __name__ == "__main__":
    sys.exit(main())

