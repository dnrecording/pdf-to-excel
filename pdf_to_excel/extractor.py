"""PDF table extraction using OCR for scanned documents."""

import os
import re
import sys
from pathlib import Path
from typing import List, Optional, Union

import pytesseract
from pdf2image import convert_from_path
from PIL import Image
from PyPDF2 import PdfReader

from .exceptions import ExtractionError, FileValidationError
from .post_processor import OCRPostProcessor


def _get_poppler_path() -> Optional[str]:
    """
    Get poppler path when running as bundled application.

    Returns:
        Path to poppler binaries if running as frozen app, None otherwise
    """
    if getattr(sys, 'frozen', False):
        # Running as bundled app
        bundle_dir = sys._MEIPASS
        print(f"[DEBUG] Running as frozen app, bundle_dir: {bundle_dir}")

        # Windows: poppler is bundled
        if sys.platform == 'win32':
            poppler_path = os.path.join(bundle_dir, 'poppler', 'bin')
            print(f"[DEBUG] Windows poppler_path: {poppler_path}")
            print(f"[DEBUG] Path exists: {os.path.exists(poppler_path)}")
            if os.path.exists(poppler_path):
                # List files in poppler directory
                try:
                    files = os.listdir(poppler_path)
                    print(f"[DEBUG] Poppler files: {files[:10]}")  # Show first 10 files
                except Exception as e:
                    print(f"[DEBUG] Error listing poppler files: {e}")
                return poppler_path
            else:
                print(f"[DEBUG] Poppler path does not exist")

        # macOS: check for bundled poppler
        elif sys.platform == 'darwin':
            poppler_path = os.path.join(bundle_dir, 'poppler', 'bin')
            print(f"[DEBUG] macOS poppler_path: {poppler_path}")
            if os.path.exists(poppler_path):
                return poppler_path
            # macOS: poppler is in Homebrew path, should be in PATH
            # Check common Homebrew locations
            for brew_path in ['/opt/homebrew/bin', '/usr/local/bin']:
                pdftoppm_path = os.path.join(brew_path, 'pdftoppm')
                if os.path.exists(pdftoppm_path):
                    print(f"[DEBUG] Found Homebrew poppler at: {brew_path}")
                    return brew_path

    return None


def pdf_needs_ocr(pdf_path: Union[str, Path]) -> bool:
    """
    Detect if a PDF contains only images (needs OCR) or has text.

    Args:
        pdf_path: Path to PDF file

    Returns:
        True if PDF needs OCR, False if it has extractable text
    """
    try:
        reader = PdfReader(str(pdf_path))

        # Check first page for text
        if len(reader.pages) > 0:
            first_page = reader.pages[0]
            text = first_page.extract_text()

            # If we get very little text, it's likely an image-based PDF
            # Threshold: less than 50 characters suggests scanned document
            return len(text.strip()) < 50

        # Empty PDF needs OCR
        return True

    except Exception as e:
        # If we can't read the PDF, assume it needs OCR
        return True


class OCRExtractor:
    """Extract text and tables from scanned PDFs using OCR."""

    def __init__(
        self,
        languages: Optional[List[str]] = None,
        ocr_mode: int = 3,
        psm_mode: int = 6,
    ):
        """
        Initialize OCR extractor.

        Args:
            languages: List of language codes (e.g., ['tha', 'eng'])
                      Defaults to Thai and English
            ocr_mode: Tesseract OCR Engine Mode
                     0 = Legacy engine only
                     1 = Neural nets LSTM engine only
                     2 = Legacy + LSTM engines
                     3 = Default (based on what is available)
            psm_mode: Page Segmentation Mode
                     3 = Fully automatic page segmentation (default)
                     4 = Assume a single column of text
                     6 = Assume a single uniform block of text
                     11 = Sparse text (find as much text as possible)
                     12 = Sparse text with OSD
        """
        if languages is None:
            languages = ["tha", "eng"]

        # Tesseract expects languages joined with '+'
        self.languages = "+".join(languages)
        self.ocr_mode = ocr_mode
        self.psm_mode = psm_mode

        # Initialize post-processor for cleaning OCR errors
        self.post_processor = OCRPostProcessor()

    def pdf_to_images(
        self, pdf_path: Union[str, Path], dpi: int = 300
    ) -> List[Image.Image]:
        """
        Convert PDF pages to images.

        Args:
            pdf_path: Path to PDF file
            dpi: Resolution for conversion (default: 300 DPI)

        Returns:
            List of PIL Image objects
        """
        try:
            # Get poppler path if running as bundled app
            poppler_path = _get_poppler_path()

            print(f"[DEBUG] Using poppler_path: {poppler_path}")

            if poppler_path:
                print(f"[DEBUG] Calling convert_from_path with poppler_path={poppler_path}")
                images = convert_from_path(
                    str(pdf_path), dpi=dpi, fmt="png", poppler_path=poppler_path
                )
            else:
                print(f"[DEBUG] Calling convert_from_path without poppler_path (using system PATH)")
                images = convert_from_path(str(pdf_path), dpi=dpi, fmt="png")

            print(f"[DEBUG] Successfully converted {len(images)} pages")
            return images
        except Exception as e:
            print(f"[DEBUG] Error in pdf_to_images: {e}")
            raise ExtractionError(f"Failed to convert PDF to images: {e}")

    def extract_text_from_image(
        self, image_path: Union[str, Path, Image.Image]
    ) -> str:
        """
        Extract text from an image using OCR.

        Args:
            image_path: Path to image file or PIL Image object

        Returns:
            Extracted text
        """
        try:
            # Configure Tesseract with custom OCR engine and PSM mode
            custom_config = f"--oem {self.ocr_mode} --psm {self.psm_mode}"

            if isinstance(image_path, (str, Path)):
                text = pytesseract.image_to_string(
                    str(image_path), lang=self.languages, config=custom_config
                )
            else:
                # PIL Image object
                text = pytesseract.image_to_string(
                    image_path, lang=self.languages, config=custom_config
                )

            return text.strip()

        except Exception as e:
            raise ExtractionError(f"Failed to extract text from image: {e}")

    def extract_text_from_pdf(self, pdf_path: Union[str, Path]) -> str:
        """
        Extract text from scanned PDF using OCR.

        Args:
            pdf_path: Path to scanned PDF

        Returns:
            Extracted text from all pages
        """
        try:
            # Convert PDF to images
            images = self.pdf_to_images(pdf_path)

            all_text = []
            for page_num, image in enumerate(images, 1):
                # Extract text from each page
                page_text = self.extract_text_from_image(image)
                if page_text:
                    all_text.append(f"--- Page {page_num} ---\n{page_text}")

            return "\n\n".join(all_text)

        except Exception as e:
            raise ExtractionError(f"Failed to extract text from PDF: {e}")

    def parse_table_from_text(self, text: str) -> Optional[List[List[str]]]:
        """
        Parse table structure from OCR text.

        This is a simple implementation that looks for rows with
        multiple spaces or tabs separating columns.

        Args:
            text: OCR extracted text

        Returns:
            List of lists representing table rows, or None if no table found
        """
        if not text or not text.strip():
            return None

        lines = text.strip().split("\n")
        table_data = []

        for line in lines:
            # Skip empty lines
            if not line.strip():
                continue

            # Split by multiple spaces (2+) or tabs
            # This is a heuristic for detecting columns
            cells = re.split(r"\s{2,}|\t+", line.strip())

            # Filter out empty cells
            cells = [cell.strip() for cell in cells if cell.strip()]

            if cells:
                table_data.append(cells)

        # Return table if we have at least 2 rows (header + data)
        return table_data if len(table_data) >= 2 else None

    def extract_tables_from_pdf(
        self, pdf_path: Union[str, Path]
    ) -> List[List[List[str]]]:
        """
        Extract all tables from scanned PDF.

        Args:
            pdf_path: Path to PDF file

        Returns:
            List of tables (each table is a list of rows)
        """
        try:
            # Extract all text
            full_text = self.extract_text_from_pdf(pdf_path)

            # Try to parse tables from text
            # For now, treat entire document as one potential table
            table = self.parse_table_from_text(full_text)

            if table:
                # Clean OCR errors in the parsed table
                table = self.post_processor.clean_table_data(table)
                return [table]
            else:
                return []

        except Exception as e:
            raise ExtractionError(f"Failed to extract tables from PDF: {e}")
