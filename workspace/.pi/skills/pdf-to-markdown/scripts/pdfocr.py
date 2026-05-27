#!/usr/bin/env python3
"""
pdfocr.py -- Convert scanned/image-based PDFs to OCR'd (searchable) PDFs.

For each input PDF, renders pages to images, runs OCR (Tesseract) on them,
and produces a new PDF with an invisible text layer over the original images.
Output is named <input_stem>.ocr.pdf.

Dependencies (beyond Tesseract CLI):
  - PyMuPDF (fitz) for PDF rendering
  - Pillow (PIL) for image handling
  - pytesseract for Tesseract Python bridge

Usage:
  python pdfocr.py <pdf-file> [<pdf-file> ...]
"""

import sys
import os
import io

import fitz  # PyMuPDF
from PIL import Image
import pytesseract


def ocr_pdf(input_path: str, output_path: str, dpi: int = 300, lang: str = "deu+eng") -> None:
    """
    Render each page of *input_path* to an image, OCR it with Tesseract,
    and write a searchable PDF to *output_path* using pytesseract's
    image_to_pdf_or_hocr output combined with the original visual page.
    """
    doc = fitz.open(input_path)
    zoom = dpi / 72.0
    scale_matrix = fitz.Matrix(zoom, zoom)

    ocr_pages = []

    for page_num in range(len(doc)):
        page = doc.load_page(page_num)
        pix = page.get_pixmap(matrix=scale_matrix)
        img_bytes = pix.tobytes("png")
        pil_img = Image.open(io.BytesIO(img_bytes))

        # Tesseract produces a searchable PDF for this page as bytes
        pdf_bytes = pytesseract.image_to_pdf_or_hocr(
            pil_img,
            lang=lang,
            extension="pdf",
            config="--psm 6"
        )
        ocr_doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        ocr_pages.append(ocr_doc)

    # Merge all single-page OCR PDFs into one output PDF
    merged = fitz.open()
    for ocr_doc in ocr_pages:
        merged.insert_pdf(ocr_doc)
        ocr_doc.close()

    merged.save(output_path, deflate=True, garbage=4)
    merged.close()
    doc.close()


def main():
    if len(sys.argv) < 2:
        print("Usage: pdfocr.py <pdf-file> [<pdf-file> ...]", file=sys.stderr)
        sys.exit(1)

    for pdf_path in sys.argv[1:]:
        pdf_path = os.path.abspath(pdf_path)
        if not os.path.isfile(pdf_path):
            print(f"[pdfocr] SKIP: not a file: {pdf_path}")
            continue

        base, _ = os.path.splitext(pdf_path)
        output_path = f"{base}.ocr.pdf"

        print(f"[pdfocr] {os.path.basename(pdf_path)} → {os.path.basename(output_path)} ...")
        ocr_pdf(pdf_path, output_path)
        print(f"[pdfocr] Done: {output_path}")


if __name__ == "__main__":
    main()
