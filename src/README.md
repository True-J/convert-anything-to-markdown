# convert-anything-md

Hybrid document-to-Markdown converter. The Python package that powers the
[convert-anything-to-markdown](https://github.com/nosliwhtes/convert-anything-to-markdown)
agent skill.

## Install

```bash
# Recommended: uv
uv tool install ./src

# Or: pipx
pipx install ./src

# Or: pip
pip install --user ./src
```

Or run the bundled cross-platform installer (uv -> pipx -> pip --user):

```bash
python3 ./src/scripts/install.py
```

Zero-install alternative: `python -m convert_anything_md <files...>`
from inside this directory (or with this directory on `PYTHONPATH`).

Works on macOS, Linux, and Windows. Pure-Python wheels only — no system
build tools required. Optional enhancements:

* `anydoc` (npm: `npm install -g @firecrawl/anydoc`) enables Rust-fast
  office document conversion (4ms median)
* `tesseract` on PATH enables OCR for scanned PDFs and image files.
* `pandoc` on PATH improves RTF extraction fidelity.

## Usage

```bash
# Single file — output to desktop (auto-detected per OS)
convert-anything-md report.pdf

# Multiple files + custom output dir
convert-anything-md -o ~/md *.pdf notes.docx

# Walk a directory recursively
convert-anything-md -r ~/Documents/inbox -o ~/md

# Force a specific engine
convert-anything-md --engine markitdown fast-preview.pdf

# List every extractor name the --engine flag accepts
convert-anything-md --list-engines

# Machine-readable output for scripts / agents
convert-anything-md --json file.pdf
```

## Supported formats

PDF (text + scanned), DOCX, PPTX, XLSX, ODT, ODS, ODP, CSV, TSV, HTML, EPUB,
RTF, MD, TXT, log, PNG, JPG, TIFF, BMP, WEBP, GIF.

## Running the tests

```bash
cd src
uv run pytest          # or: python -m pytest
```

The PDF-specific tests automatically skip when PyMuPDF (`fitz`) isn't
installed; every other test runs regardless.

## License

MIT. See the top-level LICENSE file for full text.