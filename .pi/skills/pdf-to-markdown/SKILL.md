---
name: pdf-to-markdown
description: Convert text-based and scanned PDF files to Markdown using pdfminer.six and Tesseract OCR. Uses system-wide Python packages (no venv required).
---

# PDF to Markdown

Convert PDFs to Markdown – both text-based and scanned/image PDFs.

## How it works

- Uses **system-wide Python packages** pre-installed in the Docker container:
  - `pdfminer.six` – text extraction from PDFs
  - `pymupdf` (fitz) – PDF page rendering
  - `pytesseract` – OCR for scanned documents
  - `Pillow` – image handling
  - `tesseract-ocr` – Tesseract CLI tool
- Automatically detects scanned PDFs (low text content + images)
- Runs OCR via `pdfocr.py` to create searchable PDF first
- Extracts final text to Markdown

## Requirements

This skill requires a Docker container with pre-installed dependencies:

```dockerfile
# System package
RUN apt-get install -y tesseract-ocr

# Python packages (via uv or pip)
RUN uv pip install --system pytesseract pdf2image Pillow pdfminer.six pymupdf
```

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
- For scanned PDFs: intermediate `.ocr.pdf` file is created
- Prints per-file status to stdout

## Architecture Note

This skill uses dependencies that are preinstalled in ~/.venv
All Python packages are assumed to be pre-installed in the container. This enables:
- Locked-down network access during runtime
- Consistent environment across all skills
