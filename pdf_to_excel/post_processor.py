"""Post-processing module to clean up common OCR errors."""

import re
from typing import List, Optional


class OCRPostProcessor:
    """Clean up common OCR errors in extracted text, especially for Thai accounting documents."""

    def __init__(self):
        """Initialize post-processor with pattern definitions."""
        # Common OCR misrecognitions
        self.char_replacements = {
            '~': '-',  # Tilde to minus (negative numbers)
            'O': '0',  # Letter O to zero (in numeric context)
            'l': '1',  # Lowercase L to one (in numeric context)
        }

    def clean_numeric_string(self, text: str) -> str:
        """
        Clean a string that should be a number.

        Fixes:
        - Spaces within numbers: "812, 399,00" → "812,399.00"
        - Tilde to minus: "~1,000" → "-1,000"
        - Decimal separator: ",00" → ".00"
        - Malformed thousand separators

        Args:
            text: String that should represent a number

        Returns:
            Cleaned numeric string
        """
        if not text or not text.strip():
            return text

        original = text
        text = text.strip()

        # Replace ~ with - for negative numbers
        if text.startswith('~'):
            text = '-' + text[1:].strip()  # Also remove space after ~

        # Check if this looks like a number (contains digits)
        if not re.search(r'\d', text):
            return original

        # Remove spaces within the number
        # "812, 399,00" → "812,399,00"
        text = re.sub(r'(\d)\s+(\d)', r'\1\2', text)
        text = re.sub(r'(\d)\s*,\s*(\d)', r'\1,\2', text)

        # Fix decimal separator at the end
        # "812,399,00" → "812,399.00"
        # Pattern: number ends with ",XX" where XX is 1-2 digits
        if re.search(r',\d{1,2}$', text):
            # This is likely a decimal separator
            parts = text.rsplit(',', 1)
            if len(parts) == 2 and len(parts[1]) <= 2:
                text = parts[0] + '.' + parts[1]

        # Validate thousand separators pattern
        # Should be: XXX,XXX,XXX.XX or -XXX,XXX,XXX.XX
        # Fix: "1,23,456.00" → "123,456.00" (remove incorrect separators)
        text = self._fix_thousand_separators(text)

        return text

    def _fix_thousand_separators(self, text: str) -> str:
        """
        Fix malformed thousand separators.

        Valid patterns:
        - 1,234.56
        - 12,345.67
        - 123,456.78
        - 1,234,567.89

        Invalid patterns:
        - 1,23,456.78 (inconsistent grouping)
        - 12,34,567.89

        Args:
            text: Numeric string with potential thousand separators

        Returns:
            String with corrected thousand separators
        """
        # Extract sign, digits, and decimal part
        match = re.match(r'^([-]?)([0-9,]+)(\.\d+)?$', text)
        if not match:
            return text

        sign = match.group(1)
        number_part = match.group(2)
        decimal_part = match.group(3) or ''

        # Check if number already has separators
        has_separators = ',' in number_part

        # Remove all commas
        digits_only = number_part.replace(',', '')

        # Only re-add separators if:
        # 1. The number originally had separators, OR
        # 2. The number is large enough (> 4 digits)
        if has_separators or len(digits_only) > 4:
            formatted = self._format_with_thousand_separator(digits_only)
        else:
            # Keep as-is for small numbers (like account codes)
            formatted = digits_only

        return sign + formatted + decimal_part

    def _format_with_thousand_separator(self, digits: str) -> str:
        """
        Add thousand separators to a digit string.

        Args:
            digits: String of digits without separators

        Returns:
            Formatted string with thousand separators
        """
        if len(digits) <= 3:
            return digits

        # Add commas from right to left
        parts = []
        for i in range(len(digits), 0, -3):
            start = max(0, i - 3)
            parts.append(digits[start:i])

        return ','.join(reversed(parts))

    def clean_cell(self, cell: str) -> str:
        """
        Clean a single table cell.

        Attempts to detect if cell contains numeric data and applies
        appropriate cleaning.

        Args:
            cell: Cell content as string

        Returns:
            Cleaned cell content
        """
        if not cell or not cell.strip():
            return cell

        # Check if cell looks like a pure number
        # Contains digits and common numeric characters (., ,, -, ~) without letters
        # Allow Thai characters but only if there are also numbers
        has_digits = re.search(r'\d', cell)
        has_english = re.search(r'[a-zA-Z]', cell)

        # If it has digits but no English letters, try to clean numbers within
        if has_digits and not has_english:
            # Extract all number-like patterns and clean them
            # Pattern: optional ~, then digits with spaces, commas, and periods
            # More aggressive pattern to catch numbers with spaces
            pattern = r'[~]?[\d\s,\.]+\d|[~]?\d+'

            def clean_match(match):
                num_str = match.group(0)
                # Only clean if it actually looks like a number (has digit)
                if re.search(r'\d', num_str):
                    return self.clean_numeric_string(num_str)
                return num_str

            return re.sub(pattern, clean_match, cell)

        return cell

    def clean_table_data(self, table_data: List[List[str]]) -> List[List[str]]:
        """
        Clean all cells in a parsed table.

        Args:
            table_data: List of rows, where each row is a list of cells

        Returns:
            Cleaned table data with same structure
        """
        if not table_data:
            return table_data

        cleaned_data = []
        for row in table_data:
            cleaned_row = [self.clean_cell(cell) for cell in row]
            cleaned_data.append(cleaned_row)

        return cleaned_data

    def clean_extracted_text(self, text: str) -> str:
        """
        Clean OCR-extracted text before table parsing.

        This is a lighter cleaning that preserves table structure
        but fixes obvious character misrecognitions.

        Args:
            text: Raw OCR-extracted text

        Returns:
            Cleaned text
        """
        if not text:
            return text

        # Replace common misrecognitions globally
        # Only replace ~ with - when it appears to be a negative number
        # Pattern: ~ followed by digits
        text = re.sub(r'~(\d)', r'-\1', text)

        return text
