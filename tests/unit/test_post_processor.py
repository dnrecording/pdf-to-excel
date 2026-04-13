"""Tests for OCR post-processor."""

import pytest
from pdf_to_excel.post_processor import OCRPostProcessor


class TestOCRPostProcessor:
    """Test OCR post-processing functionality."""

    @pytest.fixture
    def processor(self):
        """Create post-processor instance."""
        return OCRPostProcessor()

    def test_clean_numeric_string_removes_spaces(self, processor):
        """Test that spaces within numbers are removed."""
        # Numbers with separators - fix spacing
        assert processor.clean_numeric_string("812, 399,00") == "812,399.00"
        assert processor.clean_numeric_string("1, 234, 567.89") == "1,234,567.89"

        # Numbers without separators but large - add separators
        assert processor.clean_numeric_string("50 000.00") == "50,000.00"

    def test_clean_numeric_string_replaces_tilde_with_minus(self, processor):
        """Test that tilde is converted to minus for negative numbers."""
        assert processor.clean_numeric_string("~1,000,000.00") == "-1,000,000.00"
        assert processor.clean_numeric_string("~500.00") == "-500.00"
        assert processor.clean_numeric_string("~12,345.67") == "-12,345.67"

    def test_clean_numeric_string_fixes_decimal_separator(self, processor):
        """Test that comma decimal separators are converted to dots."""
        assert processor.clean_numeric_string("123,45") == "123.45"
        assert processor.clean_numeric_string("1,234,56") == "1,234.56"
        assert processor.clean_numeric_string("999,99") == "999.99"

    def test_clean_numeric_string_fixes_thousand_separators(self, processor):
        """Test that malformed thousand separators are fixed."""
        # Inconsistent grouping
        assert processor.clean_numeric_string("1,23,456.00") == "123,456.00"
        assert processor.clean_numeric_string("12,34,567.89") == "1,234,567.89"

        # Already correct - should remain unchanged
        assert processor.clean_numeric_string("1,234.56") == "1,234.56"
        assert processor.clean_numeric_string("123,456.78") == "123,456.78"
        assert processor.clean_numeric_string("1,234,567.89") == "1,234,567.89"

    def test_clean_numeric_string_handles_negative_numbers(self, processor):
        """Test that negative numbers are handled correctly."""
        assert processor.clean_numeric_string("-1,234.56") == "-1,234.56"
        assert processor.clean_numeric_string("~1,234.56") == "-1,234.56"
        assert processor.clean_numeric_string("~ 1,234.56") == "-1,234.56"  # Removes space after ~

    def test_clean_numeric_string_preserves_simple_numbers(self, processor):
        """Test that simple numbers (≤4 digits) are not corrupted with separators."""
        # Small numbers should not get thousand separators
        assert processor.clean_numeric_string("123") == "123"
        assert processor.clean_numeric_string("1234") == "1234"
        assert processor.clean_numeric_string("0.50") == "0.50"

        # Account codes (4 digits) should stay without separators
        assert processor.clean_numeric_string("1001") == "1001"
        assert processor.clean_numeric_string("1202") == "1202"

    def test_clean_numeric_string_handles_empty_string(self, processor):
        """Test that empty strings are handled gracefully."""
        assert processor.clean_numeric_string("") == ""
        assert processor.clean_numeric_string("   ") == "   "

    def test_clean_numeric_string_preserves_non_numeric(self, processor):
        """Test that non-numeric strings are not modified."""
        assert processor.clean_numeric_string("text") == "text"
        assert processor.clean_numeric_string("abc-123") == "abc-123"

    def test_clean_cell_applies_to_numeric_cells(self, processor):
        """Test that numeric cleaning is applied to numeric cells."""
        assert processor.clean_cell("812, 399,00") == "812,399.00"
        assert processor.clean_cell("~1,000.00") == "-1,000.00"

    def test_clean_cell_preserves_text_cells(self, processor):
        """Test that text cells are not modified."""
        assert processor.clean_cell("บริษัท มงคลสวัสดิ์") == "บริษัท มงคลสวัสดิ์"
        assert processor.clean_cell("เงินสด") == "เงินสด"
        assert processor.clean_cell("Account Name") == "Account Name"

    def test_clean_table_data(self, processor):
        """Test cleaning entire table data."""
        input_table = [
            ["รหัส", "ชื่อบัญชี", "ยอดเงิน"],
            ["1001", "เงินสด", "812, 399,00"],
            ["1002", "ธนาคาร", "~1,000,000.00"],
            ["1003", "ลูกหนี้", "50 000.00"],
        ]

        expected = [
            ["รหัส", "ชื่อบัญชี", "ยอดเงิน"],
            ["1001", "เงินสด", "812,399.00"],  # Account code preserved, money fixed
            ["1002", "ธนาคาร", "-1,000,000.00"],  # Tilde to minus
            ["1003", "ลูกหนี้", "50,000.00"],  # Spaces removed, separator added (>4 digits)
        ]

        result = processor.clean_table_data(input_table)
        assert result == expected

    def test_clean_extracted_text_replaces_tilde_before_numbers(self, processor):
        """Test that tilde is replaced with minus in extracted text."""
        text = "Account balance: ~1,500.00"
        expected = "Account balance: -1,500.00"
        assert processor.clean_extracted_text(text) == expected

    def test_format_with_thousand_separator(self, processor):
        """Test thousand separator formatting."""
        assert processor._format_with_thousand_separator("1234") == "1,234"
        assert processor._format_with_thousand_separator("123456") == "123,456"
        assert processor._format_with_thousand_separator("1234567") == "1,234,567"
        assert processor._format_with_thousand_separator("12345678") == "12,345,678"

        # Small numbers don't need separators
        assert processor._format_with_thousand_separator("123") == "123"
        assert processor._format_with_thousand_separator("12") == "12"
        assert processor._format_with_thousand_separator("1") == "1"

    def test_real_world_examples(self, processor):
        """Test with real-world OCR errors from user feedback."""
        # User feedback example 1: spaces in numbers with separators
        assert processor.clean_numeric_string("812, 399,00") == "812,399.00"

        # User feedback example 2: tilde to minus
        assert processor.clean_numeric_string("~1,000,000.00") == "-1,000,000.00"

        # Additional realistic cases
        assert processor.clean_numeric_string("26, 154.89") == "26,154.89"  # Fix spacing in separated number
        assert processor.clean_numeric_string("480 000.00") == "480,000.00"  # Large number without separator - add it
        assert processor.clean_numeric_string("~47,945.44") == "-47,945.44"  # Tilde to minus
