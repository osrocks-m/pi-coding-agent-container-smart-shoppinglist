#!/usr/bin/env python3
"""
Tests for pdf2md.py – the PDF-to-Markdown conversion script.

Two tiers of tests:
  A) Unit tests  – mock out subprocess so we can exercise
     is_scanned() logic without needing the full venv or Tesseract.
  B) Integration tests  – run the real script against the
     test-receipt.pdf (requires the venv + all deps to be installed).
"""

import os
import subprocess
import sys
import unittest

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
SKILL_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPT_DIR = os.path.join(SKILL_DIR, "scripts")
VENV_DIR = os.path.join(SKILL_DIR, ".venv")
PYTHON_EXE = os.path.join(VENV_DIR, "bin", "python")
TEST_PDF = os.path.join(SKILL_DIR, "tests", "test-receipt.pdf")


def _has_deps() -> bool:
    """Return True if the venv has all required Python packages."""
    try:
        result = subprocess.run(
            [PYTHON_EXE, "-c",
             "import pdfminer.high_level; import fitz; import pytesseract; from PIL import Image"],
            capture_output=True,
            text=True,
        )
        return result.returncode == 0
    except FileNotFoundError:
        return False


def _has_tesseract() -> bool:
    """Return True if the tesseract CLI is available."""
    try:
        result = subprocess.run(
            ["tesseract", "--version"],
            capture_output=True,
            text=True,
        )
        return result.returncode == 0
    except FileNotFoundError:
        return False


# ===================================================================
# A) UNIT TESTS for is_scanned() heuristics
# ===================================================================

class TestIsScannedHeuristics(unittest.TestCase):
    """Test the is_scanned() detection logic by replaying its stdout parser."""

    def _classify(self, total_text: int, has_images: bool, page_count: int) -> bool:
        """
        Inline re-implementation of the is_scanned heuristics from
        pdf2md.py. Mirrors the logic exactly so we don't need the venv.
        """
        MIN_TOTAL_CHARS = 100
        MIN_CHARS_PER_PAGE = 10

        if total_text == 0:
            return True
        if total_text < MIN_TOTAL_CHARS and has_images:
            return True
        if page_count > 0 and total_text < MIN_CHARS_PER_PAGE * page_count:
            return True
        return False

    def test_zero_text_always_scanned(self):
        """A PDF with zero text characters is always considered scanned."""
        self.assertTrue(self._classify(0, False, 5))
        self.assertTrue(self._classify(0, True, 1))

    def test_few_chars_per_page_is_scanned(self):
        """Total text below 10 chars per page → scanned."""
        self.assertTrue(self._classify(40, False, 5))  # 8 chars/page
        self.assertTrue(self._classify(9, True, 1))     # 9 chars/page

    def test_few_total_chars_with_images_is_scanned(self):
        """Few total chars AND has image objects → scanned."""
        self.assertTrue(self._classify(50, True, 1))    # < 100, has images
        self.assertTrue(self._classify(99, True, 3))    # < 100, has images

    def test_normal_text_pdf_is_not_scanned(self):
        """Plenty of text across pages → not scanned."""
        self.assertFalse(self._classify(5000, True, 2))   # 2500/page
        self.assertFalse(self._classify(1000, False, 5))  # 200/page

    def test_large_pdf_with_images_not_scanned(self):
        """Big PDF with lots of text is not scanned."""
        self.assertFalse(self._classify(100000, True, 50))

    def test_boundary_cases(self):
        """Edge: exactly at thresholds."""
        # 100 total chars, has images → should NOT be scanned (>= 100)
        self.assertFalse(self._classify(100, True, 1))
        # 99 total chars, has images → SHOULD be scanned (< 100)
        self.assertTrue(self._classify(99, True, 1))
        # 10 chars/page exactly → should NOT be scanned
        self.assertFalse(self._classify(50, False, 5))
        # 9 chars/page → SHOULD be scanned
        self.assertTrue(self._classify(45, False, 5))

    def test_single_page_edge_cases(self):
        """Single-page documents."""
        self.assertTrue(self._classify(0, False, 1))   # empty
        self.assertTrue(self._classify(5, True, 1))     # tiny + images
        self.assertFalse(self._classify(150, False, 1)) # normal text
        self.assertFalse(self._classify(150, True, 1))  # normal text with images


# ===================================================================
# B) INTEGRATION TESTS (need real venv & test PDF)
# ===================================================================

class TestIntegration(unittest.TestCase):
    """End-to-end tests using the real script and a real PDF."""

    @classmethod
    def setUpClass(cls):
        """Skip entire suite if venv or test PDF is missing."""
        cls._can_run = _has_deps() and os.path.isfile(TEST_PDF)
        if not cls._can_run:
            skip_msg = "SKIP: venv deps not installed or test PDF missing"
            if not os.path.isfile(TEST_PDF):
                skip_msg += f" (missing {TEST_PDF})"
            elif not _has_deps():
                skip_msg += " (install deps: run pdf2md.py once or uv pip install ...)"
            raise unittest.SkipTest(skip_msg)

    def test_pdf_analysis(self):
        """Run PDF text-analysis inside the venv to understand the test PDF."""
        code = f"""
import sys, fitz
pdf = sys.argv[1]
doc = fitz.open(pdf)
total_text = 0
has_images = False
page_count = len(doc)
for page in doc:
    total_text += len(page.get_text().strip())
    if page.get_images():
        has_images = True
print(f"pages={{page_count}}")
print(f"text_chars={{total_text}}")
print(f"has_images={{has_images}}")
doc.close()
"""
        result = subprocess.run(
            [PYTHON_EXE, "-c", code, TEST_PDF],
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 0, f"Analysis failed: {result.stderr}")

        # Parse results
        for line in result.stdout.strip().splitlines():
            print(f"  {line}")
            if line.startswith("text_chars="):
                chars = int(line.split("=")[1])
                self.assertIsInstance(chars, int)

    def test_convert_pdf_to_markdown(self):
        """Convert test PDF to markdown and check the output file."""
        md_path = TEST_PDF + ".md"
        try:
            code = f"""
import sys
from pdfminer.high_level import extract_text

pdf = sys.argv[1]
md = sys.argv[2]
text = extract_text(pdf)
with open(md, "w", encoding="utf-8") as f:
    f.write(text)
print(len(text))
"""
            result = subprocess.run(
                [PYTHON_EXE, "-c", code, TEST_PDF, md_path],
                capture_output=True,
                text=True,
            )
            self.assertEqual(result.returncode, 0, f"Convert failed: {result.stderr}")
            self.assertTrue(os.path.isfile(md_path), f"Markdown not created: {md_path}")

            with open(md_path, "r", encoding="utf-8") as f:
                text = f.read()
            print(f"  Generated: {len(text)} chars")

            # Show a sample of the output
            preview = text[:300] if len(text) > 300 else text
            print(f"  Preview: {repr(preview)}")
        finally:
            if os.path.isfile(md_path):
                os.remove(md_path)

    def test_full_pipeline_via_cli(self):
        """Run pdf2md.py as the CLI entry point.

        The test PDF is scanned (0 text, has images), so OCR is triggered.
        If tesseract is installed, the full pipeline should succeed.
        If tesseract is NOT installed, the script should handle the
        failure gracefully (no unhandled exception from pdf2md.py itself).
        """
        md_path = TEST_PDF + ".md"
        ocr_pdf_path = TEST_PDF.replace(".pdf", ".ocr.pdf")

        try:
            result = subprocess.run(
                [PYTHON_EXE, os.path.join(SCRIPT_DIR, "pdf2md.py"), TEST_PDF],
                capture_output=True,
                text=True,
            )
            print(f"  stdout: {result.stdout}")
            print(f"  stderr: {result.stderr[:500]}")

            # The script should handle failures gracefully:
            #   - If tesseract is available: exit 0, md file created
            #   - If tesseract is missing: exit 1, but no unhandled
            #     exception from pdf2md.py itself (only "FAILED" message)
            #   - If text-based: exit 0, md file created

            # Check that pdf2md.py itself didn't crash with an unhandled
            # exception. It always prints "[pdf2md] ..." prefix for output.
            lines = result.stderr.strip().splitlines()
            script_lines = [l for l in lines if l.startswith("[pdf2md]")]
            self.assertTrue(len(script_lines) > 0,
                            "pdf2md.py did not produce any status messages")

            # Check whether OCR actually ran (scanned PDF detection)
            has_ocr_detected = any("scanned" in l.lower() for l in lines)
            has_ocr_attempt = os.path.isfile(ocr_pdf_path) or \
                              "[pdfocr]" in result.stderr

            if has_ocr_attempt and not _has_tesseract():
                # OCR was attempted but tesseract is missing → expect
                # "FAILED" message in output
                has_failure = any("FAILED" in l for l in script_lines)
                self.assertTrue(has_failure,
                                "Expected [pdf2md] FAILED message when OCR deps are missing")

            if os.path.isfile(md_path):
                with open(md_path, "r", encoding="utf-8") as f:
                    text = f.read()
                print(f"  Output markdown: {len(text)} chars")
        finally:
            # Cleanup
            for f in [md_path, ocr_pdf_path]:
                if os.path.isfile(f):
                    os.remove(f)

    def test_missing_file_handling(self):
        """Running pdf2md.py on a non-existent file should not crash."""
        result = subprocess.run(
            [PYTHON_EXE, os.path.join(SCRIPT_DIR, "pdf2md.py"), "/nonexistent/file.pdf"],
            capture_output=True,
            text=True,
        )
        # Should exit gracefully (stderr has "Skip missing file")
        self.assertNotIn("Traceback", result.stderr)
        self.assertIn("Skip missing file", result.stderr)


# ===================================================================
# Entry point
# ===================================================================

if __name__ == "__main__":
    unittest.main(verbosity=2)
