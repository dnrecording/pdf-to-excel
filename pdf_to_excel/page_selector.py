"""Page selection utilities for PDF to Excel conversion.

This module provides functions to parse, validate, and optimize page selections
for PDF conversion.
"""

import re
from typing import List, Optional, Tuple, Union
from pathlib import Path

from PyPDF2 import PdfReader

from .exceptions import FileValidationError


def parse_page_selection(page_input: str) -> Optional[List[int]]:
    """Parse page selection string into a list of page numbers.

    Supported formats:
        - Single page: "1"
        - Range: "1-3" (pages 1, 2, 3)
        - Multiple: "1,3,5" (pages 1, 3, 5)
        - Combined: "1,3,5-7" (pages 1, 3, 5, 6, 7)

    Args:
        page_input: String representing page selection

    Returns:
        List of page numbers (1-based, sorted, deduplicated), or None if empty

    Raises:
        FileValidationError: If page selection syntax is invalid

    Examples:
        >>> parse_page_selection("1")
        [1]
        >>> parse_page_selection("1-3")
        [1, 2, 3]
        >>> parse_page_selection("1,3,5-7")
        [1, 3, 5, 6, 7]
        >>> parse_page_selection("")
        None
    """
    # Remove whitespace
    page_input = page_input.strip()

    # Empty string means all pages
    if not page_input:
        return None

    # Validate basic syntax
    if page_input.startswith("-"):
        raise FileValidationError(
            f"Invalid page selection: '{page_input}'. "
            "Page numbers must be positive integers."
        )

    if page_input.startswith(","):
        raise FileValidationError(
            f"Invalid page selection: '{page_input}'. "
            "Expected format like '1', '1-3', or '1,3,5-7'"
        )

    if page_input.endswith(","):
        raise FileValidationError(
            f"Invalid page selection: '{page_input}'. "
            "Trailing comma is not allowed."
        )

    # Split by comma to get individual page specifications
    page_specs = [spec.strip() for spec in page_input.split(",")]

    pages = []

    for spec in page_specs:
        if not spec:
            raise FileValidationError(
                f"Invalid page selection: '{page_input}'. "
                "Empty page specification found."
            )

        # Check for negative numbers (starts with dash)
        if spec.startswith("-"):
            raise FileValidationError(
                f"Page numbers must be positive integers. "
                f"Found invalid page: '{spec}'."
            )

        # Check if it's a range (contains dash)
        if "-" in spec:
            parts = spec.split("-")

            # Validate range format
            if len(parts) != 2:
                raise FileValidationError(
                    f"Invalid page range: '{spec}'. "
                    "Expected format like '1-3'."
                )

            start_str, end_str = parts
            start_str = start_str.strip()
            end_str = end_str.strip()

            # Validate that parts are numeric
            try:
                start = int(start_str)
                end = int(end_str)
            except ValueError:
                raise FileValidationError(
                    f"Invalid page number in range '{spec}'. "
                    "Page numbers must be integers."
                )

            # Validate positive numbers
            if start <= 0 or end <= 0:
                raise FileValidationError(
                    f"Page numbers must be positive integers. "
                    f"Found invalid range: '{spec}'."
                )

            # Normalize reverse ranges (5-1 becomes 1-5)
            if start > end:
                start, end = end, start

            # Add all pages in range
            pages.extend(range(start, end + 1))

        else:
            # Single page number
            try:
                page = int(spec)
            except ValueError:
                raise FileValidationError(
                    f"Invalid page number: '{spec}'. "
                    "Page numbers must be integers."
                )

            # Validate positive number
            if page <= 0:
                raise FileValidationError(
                    f"Page numbers must be positive integers. "
                    f"Found invalid page: {page}."
                )

            pages.append(page)

    # Remove duplicates and sort
    pages = sorted(set(pages))

    return pages


def validate_page_selection(
    pages: List[int], total_pages: int
) -> List[int]:
    """Validate that selected pages are within PDF page count.

    Args:
        pages: List of page numbers (1-based)
        total_pages: Total number of pages in PDF

    Returns:
        List of valid page numbers (out-of-range pages filtered out)

    Raises:
        FileValidationError: If no valid pages remain after filtering

    Examples:
        >>> validate_page_selection([1, 2, 3], 5)
        [1, 2, 3]
        >>> validate_page_selection([1, 3, 10], 5)
        [1, 3]
        >>> validate_page_selection([10, 20], 5)
        Raises FileValidationError
    """
    if not pages:
        return []

    # Filter valid pages
    valid_pages = [p for p in pages if 1 <= p <= total_pages]

    # Check if any valid pages remain
    if not valid_pages:
        if len(pages) == 1:
            raise FileValidationError(
                f"Page {pages[0]} is out of range. "
                f"PDF has only {total_pages} page(s)."
            )
        else:
            raise FileValidationError(
                f"No valid pages selected. PDF has only {total_pages} page(s), "
                f"but requested pages: {', '.join(map(str, pages))}"
            )

    return valid_pages


def get_page_ranges(pages: List[int]) -> List[Tuple[int, int]]:
    """Convert list of pages into list of contiguous ranges.

    This optimizes PDF conversion by grouping consecutive pages into ranges,
    reducing the number of convert_from_path() calls needed.

    Args:
        pages: List of page numbers (must be sorted)

    Returns:
        List of (start, end) tuples representing contiguous ranges

    Examples:
        >>> get_page_ranges([1])
        [(1, 1)]
        >>> get_page_ranges([1, 2, 3, 4, 5])
        [(1, 5)]
        >>> get_page_ranges([1, 3, 4, 5, 7])
        [(1, 1), (3, 5), (7, 7)]
    """
    if not pages:
        return []

    ranges = []
    start = pages[0]
    end = pages[0]

    for i in range(1, len(pages)):
        if pages[i] == end + 1:
            # Contiguous page, extend current range
            end = pages[i]
        else:
            # Gap found, save current range and start new one
            ranges.append((start, end))
            start = pages[i]
            end = pages[i]

    # Add the last range
    ranges.append((start, end))

    return ranges


def get_pdf_page_count(pdf_path: Union[str, Path]) -> int:
    """Get the total number of pages in a PDF file.

    Args:
        pdf_path: Path to PDF file

    Returns:
        Total number of pages

    Raises:
        FileValidationError: If PDF cannot be read

    Examples:
        >>> get_pdf_page_count("document.pdf")
        5
    """
    try:
        with open(pdf_path, "rb") as f:
            reader = PdfReader(f)
            return len(reader.pages)
    except Exception as e:
        raise FileValidationError(
            f"Cannot read PDF file '{pdf_path}': {str(e)}"
        )
