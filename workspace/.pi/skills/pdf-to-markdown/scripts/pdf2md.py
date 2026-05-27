#!/usr/bin/env python3
"""
pdf2md.py -- Convert PDFs to Markdown using pdfminer.six.

Automatically detects scanned/image-based PDFs and OCRs them first using
pdfocr.py (produces <name>.ocr.pdf), then extracts text to Markdown.
"""
import os
import subprocess
import sys

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
SKILL_DIR = os.path.dirname(SCRIPT_DIR)
# Use system-wide venv at /home/node/.venv (created in Dockerfile)
VENV_DIR = os.path.expanduser("~/.venv")
PYTHON_EXE = os.path.join(VENV_DIR, "bin", "python")
_UV_CANDIDATES = [
    "uv",
    os.path.expanduser("~/.local/bin/uv"),
    "/usr/local/bin/uv",
    "/opt/uv/uv",
]


UV_EXE = None


def _find_uv():
    global UV_EXE
    if UV_EXE:
        return UV_EXE
    for candidate in _UV_CANDIDATES:
        try:
            if subprocess.run(
                [candidate, "--version"], capture_output=True
            ).returncode == 0:
                UV_EXE = candidate
                return candidate
        except (FileNotFoundError, OSError):
            continue
    return None


def _ensure_venv():
    if not os.path.isfile(PYTHON_EXE):
        uv = _find_uv()
        if uv is None:
            print(
                "[pdf2md] error: 'uv' is required but not found.",
                file=sys.stderr,
            )
            sys.exit(1)
        subprocess.run([uv, "venv", VENV_DIR], check=True)


def _ensure_deps():
    uv = _find_uv()

    # pdfminer.six
    try:
        subprocess.run(
            [PYTHON_EXE, "-c", "import pdfminer.high_level"],
            check=True, capture_output=True,
        )
    except subprocess.CalledProcessError:
        subprocess.run(
            [uv, "pip", "install", "--python", PYTHON_EXE, "pdfminer.six"],
            check=True,
        )

    # pymupdf (for PyMuPDF / fitz)
    try:
        subprocess.run(
            [PYTHON_EXE, "-c", "import fitz"],
            check=True, capture_output=True,
        )
    except subprocess.CalledProcessError:
        subprocess.run(
            [uv, "pip", "install", "--python", PYTHON_EXE, "pymupdf"],
            check=True,
        )

    # pytesseract + Pillow (for OCR)
    try:
        subprocess.run(
            [PYTHON_EXE, "-c", "import pytesseract"],
            check=True, capture_output=True,
        )
    except subprocess.CalledProcessError:
        subprocess.run(
            [uv, "pip", "install", "--python", PYTHON_EXE, "pytesseract"],
            check=True,
        )

    try:
        subprocess.run(
            [PYTHON_EXE, "-c", "from PIL import Image"],
            check=True, capture_output=True,
        )
    except subprocess.CalledProcessError:
        subprocess.run(
            [uv, "pip", "install", "--python", PYTHON_EXE, "Pillow"],
            check=True,
        )


def is_scanned(pdf_path):
    """Return True if pdf_path appears to be an image-only / scanned PDF."""
    code = """
import sys, fitz
pdf = sys.argv[1]
doc = fitz.open(pdf)
total_text = 0
has_images = False
for page in doc:
    total_text += len(page.get_text().strip())
    if page.get_images():
        has_images = True
print(total_text)
print("1" if has_images else "0")
print(len(doc))
doc.close()
"""
    result = subprocess.run(
        [PYTHON_EXE, "-c", code, pdf_path],
        capture_output=True, text=True,
    )
    if result.returncode != 0:
        # If analysis fails, conservatively assume not scanned
        return False

    lines = result.stdout.strip().splitlines()
    total_text = int(lines[0])
    has_images = lines[1] == "1"
    page_count = int(lines[2])

    MIN_TOTAL_CHARS = 100
    MIN_CHARS_PER_PAGE = 10

    if total_text == 0:
        return True
    if total_text < MIN_TOTAL_CHARS and has_images:
        return True
    if page_count > 0 and total_text < MIN_CHARS_PER_PAGE * page_count:
        return True
    return False


def convert(pdf_path, md_path=None):
    if md_path is None:
        md_path = os.path.splitext(pdf_path)[0] + ".md"
    code = """
import os, sys
from pdfminer.high_level import extract_text

pdf = sys.argv[1]
md = sys.argv[2]
text = extract_text(pdf)
with open(md, "w", encoding="utf-8") as f:
    f.write(text)
print(md + "\\t" + str(len(text)))
"""
    result = subprocess.run(
        [PYTHON_EXE, "-c", code, pdf_path, md_path],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip())
    parts = result.stdout.strip().split("\t")
    return parts[0], int(parts[1])


def main(argv):
    if len(argv) < 2:
        print("Usage: python3 pdf2md.py <pdf> [<pdf> ...]", file=sys.stderr)
        return 1

    _ensure_venv()
    _ensure_deps()

    ok = 0
    for pdf in argv[1:]:
        if not os.path.isfile(pdf):
            print(f"[pdf2md] Skip missing file: {pdf}", file=sys.stderr)
            continue
        try:
            scanned = is_scanned(pdf)
            source_pdf = pdf
            if scanned:
                ocr_pdf = os.path.splitext(pdf)[0] + ".ocr.pdf"
                if not os.path.isfile(ocr_pdf):
                    print(f"[pdf2md] Detected scanned PDF, running OCR: {pdf}")
                    ocr_script = os.path.join(SCRIPT_DIR, "pdfocr.py")
                    subprocess.run([PYTHON_EXE, ocr_script, pdf], check=True)
                source_pdf = ocr_pdf

            md_target = os.path.splitext(pdf)[0] + ".md"
            md_path, length = convert(source_pdf, md_target)
            print(f"[pdf2md] {pdf} -> {md_path} ({length} chars)")
            ok += 1
        except Exception as e:
            print(f"[pdf2md] FAILED {pdf}: {e}", file=sys.stderr)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
