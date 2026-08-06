# Example: batch conversion of mixed formats

Convert an entire folder of mixed-format documents in one command. Each
file is routed to the extractor best suited to its format — errors on
one file don't abort the rest of the batch.

## Input

```
~/Downloads/project/
├── kickoff.docx
├── budget.xlsx
├── slides.pptx
├── research.pdf
├── readme.md
└── whiteboard.png       # photo of a whiteboard
```

## Command

```bash
convert-anything-md ~/Downloads/project/*
```

Or, from inside the folder:

```bash
cd ~/Downloads/project
convert-anything-md *
```

## Output

Six Markdown files land on the desktop:

```
~/Desktop/kickoff.md       (engine: docling,   2 pages)
~/Desktop/budget.md        (engine: docling,   3 sheets)
~/Desktop/slides.md        (engine: docling,  18 slides)
~/Desktop/research.md      (engine: docling,  40 pages)
~/Desktop/readme.md        (engine: markdown-passthrough)
~/Desktop/whiteboard.md    (engine: tesseract)
```

## Sample interactive table

```
convert-anything-md v1.0.0

Source          Kind       Engine                   Pages  Words   Time   Output
kickoff.docx    docx       docling                    —    1,204   0.8s   ~/Desktop/kickoff.md
budget.xlsx     xlsx       docling                    —      312   1.1s   ~/Desktop/budget.md
slides.pptx     pptx       docling                   18    1,877   1.5s   ~/Desktop/slides.md
research.pdf    pdf_text   docling                   40    8,412   2.9s   ~/Desktop/research.md
readme.md       markdown   markdown-passthrough       —      201   0.0s   ~/Desktop/readme.md
whiteboard.png  image      tesseract                  —       67   0.4s   ~/Desktop/whiteboard.md
```

## Mixed-success scenarios

If one file fails (e.g. corrupted XLSX), the batch still finishes and
the CLI exits with code `1` to signal partial failure:

```
budget.xlsx  xlsx  FAILED  —  —  —  openpyxl failed: corrupt workbook header
```

In `--json` mode, the `results[]` array contains both successful and
failed entries, and `summary.failed` is non-zero. This lets the calling
skill report cleanly to the user:

> Converted 5 of 6 files. One failure:
> • `budget.xlsx` — "corrupt workbook header". Try re-saving in Excel first.

