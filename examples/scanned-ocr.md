# Example: scanned PDF (OCR)

The router detects that a PDF has no embedded text layer and routes it
to the OCR chain. No CLI flags required — detection is automatic.

## How detection works

1. The PDF opens with PyMuPDF.
2. Up to 5 evenly-spaced pages are sampled.
3. The average printable-character count per page is computed.
4. If the average is **below 100 chars/page**, the file is treated as
   scanned and routed to `pdf_ocr`.

Text-embedded PDFs yield thousands of chars per page, so this threshold
has ample margin. Edge cases (diagram-heavy PDFs with tiny captions)
that get mis-classified can be overridden with `--engine docling`.

## Input

```
~/Downloads/scanned-invoice.pdf       # 3-page scan, no text layer
```

## Command

```bash
convert-anything-md ~/Downloads/scanned-invoice.pdf
```

## What happens

* Detection: `pdf_scanned`
* Chain attempted: `pdf_ocr → docling → markitdown`
* Winner: `pdf_ocr` (rasterize via PyMuPDF at 300 dpi, OCR each page with
  Tesseract, stitch into Markdown with `## Page N` headings).

## Output

`~/Desktop/scanned-invoice.md`:

```yaml
---
source: /path/to/user/Downloads/scanned-invoice.pdf
source_name: scanned-invoice.pdf
engine: pdf_ocr
fallback_chain: [pdf_ocr]
pages: 3
word_count: 412
duration_ms: 5400
warnings: []
ocr_dpi: 300
---

## Page 1

ACME Corp Invoice #12345
Bill To: ...
...

## Page 2

Line Items
...

## Page 3

Total Due: $1,234.00
...
```

## Troubleshooting

If Tesseract isn't installed, the outcome will be:

```
FAILED  —  tesseract binary missing. Install:
         macOS → `brew install tesseract`;
         Linux → `apt/dnf/pacman install tesseract-ocr`;
         Windows → https://github.com/UB-Mannheim/tesseract/wiki
```

Install Tesseract, re-run, and you're back in business.

