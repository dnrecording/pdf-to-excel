"""Tests for page selection parsing and validation."""

import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

from pdf_to_excel.page_selector import (
    parse_page_selection,
    validate_page_selection,
    get_page_ranges,
    get_pdf_page_count,
)
from pdf_to_excel.exceptions import FileValidationError


class TestParsePageSelection:
    """Tests for parse_page_selection function."""

    def test_single_page(self):
        """Test parsing a single page number."""
        assert parse_page_selection("1") == [1]
        assert parse_page_selection("5") == [5]

    def test_simple_range(self):
        """Test parsing a simple page range."""
        assert parse_page_selection("1-3") == [1, 2, 3]
        assert parse_page_selection("5-8") == [5, 6, 7, 8]

    def test_multiple_pages(self):
        """Test parsing multiple individual pages."""
        assert parse_page_selection("1,3,5") == [1, 3, 5]
        assert parse_page_selection("2,4,6,8") == [2, 4, 6, 8]

    def test_combined_pages_and_ranges(self):
        """Test parsing combination of pages and ranges."""
        assert parse_page_selection("1,3,5-7") == [1, 3, 5, 6, 7]
        assert parse_page_selection("1-3,5,7-9") == [1, 2, 3, 5, 7, 8, 9]

    def test_complex_selection(self):
        """Test parsing complex page selection."""
        assert parse_page_selection("1-3,5,7-9,11") == [1, 2, 3, 5, 7, 8, 9, 11]

    def test_empty_string_returns_none(self):
        """Test that empty string returns None (all pages)."""
        assert parse_page_selection("") is None
        assert parse_page_selection("   ") is None

    def test_whitespace_handling(self):
        """Test handling of whitespace in input."""
        assert parse_page_selection(" 1, 3, 5 - 7 ") == [1, 3, 5, 6, 7]
        assert parse_page_selection("1 - 3") == [1, 2, 3]

    def test_reverse_range(self):
        """Test that reverse ranges are normalized."""
        assert parse_page_selection("5-1") == [1, 2, 3, 4, 5]
        assert parse_page_selection("10-5") == [5, 6, 7, 8, 9, 10]

    def test_duplicate_pages_removed(self):
        """Test that duplicate pages are removed."""
        assert parse_page_selection("1,1,2,2-4") == [1, 2, 3, 4]
        assert parse_page_selection("1-3,2-4") == [1, 2, 3, 4]

    def test_single_page_range(self):
        """Test range with same start and end."""
        assert parse_page_selection("3-3") == [3]

    def test_pages_are_sorted(self):
        """Test that pages are returned in sorted order."""
        assert parse_page_selection("5,1,3") == [1, 3, 5]
        assert parse_page_selection("10,5,1,3") == [1, 3, 5, 10]

    def test_invalid_syntax_multiple_dashes(self):
        """Test error on invalid syntax with multiple dashes."""
        with pytest.raises(FileValidationError, match="Invalid page range"):
            parse_page_selection("1-2-3")

    def test_invalid_syntax_trailing_comma(self):
        """Test error on trailing comma."""
        with pytest.raises(FileValidationError, match="Invalid page selection"):
            parse_page_selection("1,")

    def test_invalid_syntax_leading_dash(self):
        """Test error on leading dash."""
        with pytest.raises(FileValidationError, match="Invalid page selection"):
            parse_page_selection("-5")

    def test_invalid_syntax_non_numeric(self):
        """Test error on non-numeric input."""
        with pytest.raises(FileValidationError, match="Invalid page number"):
            parse_page_selection("abc")
        with pytest.raises(FileValidationError, match="Invalid page number"):
            parse_page_selection("1,abc,3")

    def test_invalid_syntax_decimal(self):
        """Test error on decimal numbers."""
        with pytest.raises(FileValidationError, match="Invalid page number"):
            parse_page_selection("1.5")
        with pytest.raises(FileValidationError, match="Invalid page number"):
            parse_page_selection("1,2.5,3")

    def test_zero_page_raises_error(self):
        """Test that page 0 raises an error."""
        with pytest.raises(FileValidationError, match="Page numbers must be positive"):
            parse_page_selection("0")
        with pytest.raises(FileValidationError, match="Page numbers must be positive"):
            parse_page_selection("0-5")

    def test_negative_page_raises_error(self):
        """Test that negative pages raise an error."""
        with pytest.raises(FileValidationError, match="Page numbers must be positive"):
            parse_page_selection("-1")
        with pytest.raises(FileValidationError, match="Page numbers must be positive"):
            parse_page_selection("1,-3,5")


class TestValidatePageSelection:
    """Tests for validate_page_selection function."""

    def test_all_pages_valid(self):
        """Test validation when all pages are within range."""
        pages = [1, 2, 3]
        assert validate_page_selection(pages, total_pages=5) == [1, 2, 3]

    def test_filter_out_of_range_pages(self):
        """Test that out-of-range pages are filtered."""
        pages = [1, 3, 10]
        assert validate_page_selection(pages, total_pages=5) == [1, 3]

    def test_all_pages_out_of_range_raises_error(self):
        """Test error when all pages are out of range."""
        pages = [10, 20, 30]
        with pytest.raises(FileValidationError, match="No valid pages"):
            validate_page_selection(pages, total_pages=5)

    def test_empty_list_returns_empty(self):
        """Test that empty list returns empty list."""
        assert validate_page_selection([], total_pages=5) == []

    def test_single_valid_page(self):
        """Test validation with single valid page."""
        pages = [3]
        assert validate_page_selection(pages, total_pages=5) == [3]

    def test_single_invalid_page_raises_error(self):
        """Test error when single page is out of range."""
        pages = [10]
        with pytest.raises(FileValidationError, match="Page 10 is out of range"):
            validate_page_selection(pages, total_pages=5)


class TestGetPageRanges:
    """Tests for get_page_ranges function."""

    def test_single_page(self):
        """Test single page returns single range."""
        assert get_page_ranges([1]) == [(1, 1)]
        assert get_page_ranges([5]) == [(5, 5)]

    def test_contiguous_range(self):
        """Test contiguous pages return single range."""
        assert get_page_ranges([1, 2, 3, 4, 5]) == [(1, 5)]
        assert get_page_ranges([3, 4, 5]) == [(3, 5)]

    def test_non_contiguous_pages(self):
        """Test non-contiguous pages return multiple ranges."""
        assert get_page_ranges([1, 3, 5, 7]) == [(1, 1), (3, 3), (5, 5), (7, 7)]

    def test_mixed_ranges_and_singles(self):
        """Test mix of contiguous and non-contiguous pages."""
        assert get_page_ranges([1, 3, 4, 5, 7]) == [(1, 1), (3, 5), (7, 7)]
        assert get_page_ranges([1, 2, 5, 6, 7, 10]) == [(1, 2), (5, 7), (10, 10)]

    def test_two_page_range(self):
        """Test two consecutive pages."""
        assert get_page_ranges([1, 2]) == [(1, 2)]

    def test_empty_list(self):
        """Test empty list returns empty list."""
        assert get_page_ranges([]) == []


class TestGetPdfPageCount:
    """Tests for get_pdf_page_count function."""

    @patch("pdf_to_excel.page_selector.PdfReader")
    def test_valid_pdf_returns_page_count(self, mock_pdf_reader):
        """Test getting page count from valid PDF."""
        # Mock PdfReader
        mock_reader = MagicMock()
        mock_reader.pages = [None] * 5  # 5 pages
        mock_pdf_reader.return_value = mock_reader

        count = get_pdf_page_count("test.pdf")
        assert count == 5

    @patch("pdf_to_excel.page_selector.PdfReader")
    def test_single_page_pdf(self, mock_pdf_reader):
        """Test getting page count from single-page PDF."""
        mock_reader = MagicMock()
        mock_reader.pages = [None]  # 1 page
        mock_pdf_reader.return_value = mock_reader

        count = get_pdf_page_count("test.pdf")
        assert count == 1

    @patch("pdf_to_excel.page_selector.PdfReader")
    def test_corrupted_pdf_raises_error(self, mock_pdf_reader):
        """Test error handling for corrupted PDF."""
        mock_pdf_reader.side_effect = Exception("PDF is corrupted")

        with pytest.raises(FileValidationError, match="Cannot read PDF"):
            get_pdf_page_count("corrupted.pdf")

    @patch("pdf_to_excel.page_selector.PdfReader")
    def test_accepts_path_object(self, mock_pdf_reader):
        """Test that function accepts Path objects."""
        mock_reader = MagicMock()
        mock_reader.pages = [None] * 3
        mock_pdf_reader.return_value = mock_reader

        path = Path("test.pdf")
        count = get_pdf_page_count(path)
        assert count == 3
