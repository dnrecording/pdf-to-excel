"""PDF to Excel Converter

A Python library for extracting tables from PDF files (including scanned documents)
and converting them to well-formatted Excel spreadsheets with Thai language support.
"""

__version__ = "0.1.0"

from .exceptions import (
    PDFToExcelError,
    FileValidationError,
    InvalidFileFormatError,
    CorruptPDFError,
    ExtractionError,
    ProcessingError,
    WriterError,
)
from .utils import validate_pdf_file
from .extractor import OCRExtractor, pdf_needs_ocr

__all__ = [
    "PDFToExcelError",
    "FileValidationError",
    "InvalidFileFormatError",
    "CorruptPDFError",
    "ExtractionError",
    "ProcessingError",
    "WriterError",
    "validate_pdf_file",
    "OCRExtractor",
    "pdf_needs_ocr",
]
