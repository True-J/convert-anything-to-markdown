# Extractor selection rationale

Decisions made for v1.0.0. Research conducted April 2026.

## PDF (text-embedded)

**Primary: Docling (IBM).** Recent benchmarks (early 2025) put Docling
at 97.9% accuracy on complex table extraction, substantially ahead of
MarkItDown, pymupdf4llm, and Unstructured on layout-heavy PDFs.

**Fallback: MarkItDown (Microsoft).** Much faster because it doesn't
load ML models. Good enough for straight text pages. Acceptable when
Docling is missing or errors out.

**Last-resort: pdf_ocr chain.** If both text-based extractors return
empty/garbage (very rare — usually a detection miss), the OCR path is
tried.

## PDF (scanned, no text)

**Primary: pdf_ocr (PyMuPDF + Tesseract).** We chose PyMuPDF over
`pdf2image` + poppler because PyMuPDF ships as a pure-wheel install on
all OSes. Windows users in particular get a working OCR path without
installing poppler separately.

Rasterization happens at 300 dpi (industry-standard for OCR accuracy vs
memory use). Each page gets an `## Page N` heading in the output for
easy navigation.

**Fallback: Docling.** Docling's OCR mode is excellent when available
but depends on the optional `[ocr]` extras.

## DOCX / PPTX / XLSX

**Primary: Docling.** Handles all three natively with strong structure
preservation.

**Fallback: MarkItDown.** Faster, no ML models; preserves most content
but flattens some tables.

**Last-resort: pure-Python** (`python-docx`, `python-pptx`, `openpyxl`).
Wheel-only and works in the most restricted environments. Less
polished output — we preserve headings and tables but drop things like
embedded charts and shapes.

## CSV / TSV

**Primary: the Python stdlib `csv` module.** Zero deps, perfect for
simple tabular data. Outputs a GitHub-flavored Markdown table. Uses
`csv.Sniffer` to handle weird delimiters.

**Fallback: MarkItDown.** For the rare case where the file looks like
CSV but has structural quirks (multi-header rows, embedded quotes)
that our table renderer trips on.

## HTML

**Primary: Trafilatura.** Measured F1 of 0.958 on news-style pages —
outperforms readability-lxml (0.947) and jusText. Handles boilerplate
removal well.

**Fallback: MarkItDown.** Good general HTML support, weaker on messy
modern JS-framework output.

**Last-resort: BeautifulSoup walk.** A simple tag-to-Markdown mapping
when both of the above fail or aren't installed.

## EPUB

**Primary: ebooklib + BeautifulSoup.** EPUB is structurally a zip of
XHTML; walking the spine with ebooklib and reducing each chapter to
plain Markdown is both fast and reliable.

**Fallback: MarkItDown.** Works for simpler EPUBs.

Why not pandoc as primary? Pandoc is fantastic but adds a mandatory
binary dependency that Windows users frequently don't have. ebooklib
stays in the pure-Python lane.

## RTF

**Primary: pandoc.** Best RTF fidelity bar none — handles tables,
styles, and embedded content that pure-Python parsers drop.

**Fallback: striprtf.** A tiny pure-Python library that handles RTF
well enough for plain-text use cases. Keeps Windows users (often sans
pandoc) functional.

**Last-resort: MarkItDown.** General-purpose safety net.

## TXT / MD / log

**Direct passthrough.** TXT files get wrapped in a minimal `# Heading`
+ fenced code block so they render cleanly in Markdown viewers. MD
files are preserved as-is (with normalized trailing newline). Zero
dependencies, sub-millisecond conversion.

## Images (PNG, JPG, TIFF, BMP, WEBP, GIF)

**Primary: Tesseract.** The default open-source OCR engine. Pillow
handles format decoding before passing to `pytesseract`.

No fallback. If Tesseract isn't installed, the extractor raises
`ExtractorUnavailable` with an OS-specific install hint.

## Deferred to later versions

| Format           | Why not in v1                                |
|------------------|----------------------------------------------|
| URLs (http/s)    | Requires network policy decisions & caching |
| Audio / video    | Whisper is heavy; deserves its own toggle    |
| YouTube          | Same as audio + terms-of-service concerns    |
| ZIP (recursive)  | Potential runaway extraction; needs a cap    |
| MOBI / AZW       | ebooklib support is partial; calibre-needed  |
| .eml / mbox      | No clean-input standard — messy source       |

