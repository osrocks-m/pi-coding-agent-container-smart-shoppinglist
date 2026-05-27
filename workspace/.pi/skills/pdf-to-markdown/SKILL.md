---
name: pdf-to-markdown
description: Convert text-based PDF files to Markdown using pdfminer.six. Installs dependencies with uv into a dedicated venv when first used.
---

# PDF to Markdown

Convert text-based PDFs to Markdown without needing system tools like `pdftotext` or `pandoc`.

## How it works

- Uses `uv` to create a dedicated virtual environment under the skill directory
- Installs `pdfminer.six` via `uv pip install` on first use
- Extracts text with `pdfminer.high_level.extract_text(...)`
- Writes one `<basename>.md` per input PDF

## Requirements

`uv` must be available. The script looks for it in your PATH, `~/.local/bin/uv`, `/usr/local/bin/uv`, and `/opt/uv/uv`.

## Usage

```bash
./scripts/pdf2md.py <pdf-file> [<pdf-file> ...]
```

Examples:

```bash
# Single file
./scripts/pdf2md.py report.pdf

# Multiple files
./scripts/pdf2md.py file1.pdf file2.pdf

# All PDFs in current directory
./scripts/pdf2md.py *.pdf
```

## Output

- One Markdown file per PDF, named after the original file (`.pdf` → `.md`)
- Prints per-file status to stdout
