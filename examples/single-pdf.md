# Example: single PDF

The most common case. A text-embedded PDF goes through Docling for best
table and layout fidelity.

## Input

```
~/Downloads/quarterly-report.pdf       # 42-page PDF with tables
```

## Command

```bash
convert-anything-md ~/Downloads/quarterly-report.pdf
```

## Output

A `~/Desktop/quarterly-report.md` file, starting with YAML front-matter:

```yaml
---
source: /path/to/user/Downloads/quarterly-report.pdf
source_name: quarterly-report.pdf
source_sha256: a1b2c3d4e5f6...
converted_at: 2026-04-14T10:23:45-06:00
converter: convert-anything-md@1.0.0
engine: docling
fallback_chain: [docling]
pages: 42
word_count: 9847
duration_ms: 3200
warnings: []
---
```

... followed by the extracted Markdown body.

## CLI table (interactive mode)

```
convert-anything-md v1.0.0

Source                      Kind      Engine    Pages  Words   Time   Output
quarterly-report.pdf        pdf_text  docling   42     9,847   3.2s   ~/Desktop/quarterly-report.md
```

## What if Docling isn't installed?

The router automatically falls back — first to MarkItDown (fast,
text-focused), then to the PDF OCR path if text extraction yields
nothing. You'll see a warning in `-v` (verbose) mode:

```
# quarterly-report.pdf
  chain: docling → markitdown
  ⚠ docling unavailable: No module named 'docling'
```

Quality drops a bit (tables are flatter) but the job still completes.

## What if the PDF is scanned?

The router samples 5 pages; if average chars/page is below the threshold,
it automatically routes to the OCR chain (`pdf_ocr`) using PyMuPDF +
Tesseract. The output .md looks slightly different — one `## Page N`
heading per page of extracted text.

