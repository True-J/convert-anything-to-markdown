# Troubleshooting

A grab-bag of issues and fixes. Run `python3 scripts/preflight.py` first
to get a full readout of what's available on your machine.

## "convert-anything-md: command not found"

The CLI isn't on your PATH. Two likely causes:

1. **`uv tool install` succeeded but the install dir isn't in PATH.**
   * Linux/macOS: `export PATH="$HOME/.local/bin:$PATH"` in your
     shell rc.
   * Windows: `setx PATH "%PATH%;%USERPROFILE%\.local\bin"` then
     restart your terminal.
2. **Install actually failed.** Re-run:
   ```bash
   python3 scripts/install.py
   ```
   The installer tries `uv` → `pipx` → `pip --user` in order.

## "tesseract binary missing"

You'll see this when converting a scanned PDF or an image file.

* **macOS:** `brew install tesseract`
* **Linux:** `sudo apt install tesseract-ocr` (or equivalent for your
  distro: `dnf`, `pacman`, etc.)
* **Windows:** grab the installer at
  https://github.com/UB-Mannheim/tesseract/wiki. Make sure you tick
  "Add to PATH" during install.

Verify with `tesseract --version`.

## "docling failed" or first-run takes forever

Docling downloads ML models (~1-2 GB) on first use. If this stalls on
a slow connection, you have two options:

1. Wait it out once — subsequent runs are instant.
2. Force a different engine:
   ```bash
   convert-anything-md --engine markitdown file.pdf
   ```

## PDF output looks garbled

Some PDFs have non-standard character encoding. Try:

```bash
convert-anything-md --engine pdf_ocr file.pdf
```

This re-rasterizes each page and runs OCR, which bypasses encoding
issues at the cost of speed.

## Output lands in the wrong place on Linux

Linux desktops let users relocate the Desktop folder via
`~/.config/user-dirs.dirs`. We honor that; check what it says:

```bash
cat ~/.config/user-dirs.dirs | grep DESKTOP
```

If it points somewhere surprising, override with `-o`:

```bash
convert-anything-md -o ~/Desktop file.pdf
```

## Output lands in OneDrive on Windows

Windows redirects the Desktop folder to OneDrive when OneDrive is
enabled. We respect that setting because it's what `Desktop` literally
points to in the registry. If you want a local path, use `-o`:

```bash
convert-anything-md -o "%USERPROFILE%\Desktop-local" file.pdf
```

## "all extractors failed or were unavailable"

The router has no working option for this file. Two diagnostics:

1. Check the warnings list in the error — it enumerates each
   extractor tried and why it skipped.
2. Run `python3 scripts/preflight.py` to see which libraries are
   installed.

For a stubborn file, try every engine by hand:

```bash
for engine in docling markitdown pdf_ocr; do
    echo "== $engine =="
    convert-anything-md --engine "$engine" --dry-run file.pdf
done
```

## Test failures during development

If `uv run pytest` reports failures in `test_detect.py`'s PDF section,
it likely means PyMuPDF isn't installed in the dev environment. The
PDF tests are guarded by `pytest.importorskip("fitz")` and will skip
if missing — install it with `uv pip install pymupdf` to exercise them.

## Reporting bugs

Include the output of:

```bash
python3 scripts/preflight.py
convert-anything-md --version
convert-anything-md -v --dry-run <the problematic file>
```

That's usually enough to diagnose. File issues at
https://github.com/seth-wilson/convert-anything-to-markdown/issues.

