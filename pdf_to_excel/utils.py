"""Utility functions for PDF to Excel converter."""

from pathlib import Path
from typing import Union
from .exceptions import FileValidationError, InvalidFileFormatError


def validate_pdf_file(file_path: Union[str, Path]) -> bool:
    """
    Validate that a file exists and is a PDF.

    Args:
        file_path: Path to the file to validate

    Returns:
        True if file is valid

    Raises:
        FileValidationError: If file doesn't exist
        InvalidFileFormatError: If file is not a valid PDF
    """
    path = Path(file_path)

    # Check if file exists
    if not path.exists():
        raise FileValidationError(f"File not found: {file_path}")

    # Check if it's a file (not a directory)
    if not path.is_file():
        raise FileValidationError(f"Not a file: {file_path}")

    # Check if file is empty
    if path.stat().st_size == 0:
        raise InvalidFileFormatError(f"File is empty: {file_path}")

    # Check PDF header (minimal check)
    # Valid PDF files start with %PDF-
    try:
        with open(path, "rb") as f:
            header = f.read(5)
            if not header.startswith(b"%PDF-"):
                raise InvalidFileFormatError(
                    f"Not a valid PDF file (missing PDF header): {file_path}"
                )
    except IOError as e:
        raise FileValidationError(f"Cannot read file: {file_path}. Error: {e}")

    return True
