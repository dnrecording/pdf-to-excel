"""Unit tests for utility functions."""

import pytest
from pathlib import Path


@pytest.mark.unit
class TestFileValidation:
    """Tests for file validation functions."""

    def test_validate_existing_pdf_file(self, tmp_path: Path) -> None:
        """Test validation of an existing PDF file."""
        # Arrange: Create a dummy PDF file
        pdf_file = tmp_path / "test.pdf"
        pdf_file.write_bytes(b"%PDF-1.4\n%Test PDF content\n")  # Minimal PDF header

        # Act & Assert: This will fail until we implement the function
        from pdf_to_excel.utils import validate_pdf_file

        result = validate_pdf_file(str(pdf_file))
        assert result is True

    def test_validate_nonexistent_file(self) -> None:
        """Test validation of non-existent file."""
        # Arrange
        non_existent = "/path/that/does/not/exist.pdf"

        # Act & Assert
        from pdf_to_excel.utils import validate_pdf_file
        from pdf_to_excel.exceptions import FileValidationError

        with pytest.raises(FileValidationError):
            validate_pdf_file(non_existent)

    def test_validate_non_pdf_file(self, tmp_path: Path) -> None:
        """Test validation of non-PDF file (e.g., .txt)."""
        # Arrange: Create a text file
        text_file = tmp_path / "test.txt"
        text_file.write_text("This is not a PDF")

        # Act & Assert
        from pdf_to_excel.utils import validate_pdf_file
        from pdf_to_excel.exceptions import InvalidFileFormatError

        with pytest.raises(InvalidFileFormatError):
            validate_pdf_file(str(text_file))

    def test_validate_empty_file(self, tmp_path: Path) -> None:
        """Test validation of empty file with .pdf extension."""
        # Arrange: Create empty file
        empty_file = tmp_path / "empty.pdf"
        empty_file.write_bytes(b"")

        # Act & Assert
        from pdf_to_excel.utils import validate_pdf_file
        from pdf_to_excel.exceptions import InvalidFileFormatError

        with pytest.raises(InvalidFileFormatError):
            validate_pdf_file(str(empty_file))

    def test_validate_pdf_with_spaces_in_path(self, tmp_path: Path) -> None:
        """Test validation of PDF with spaces in filename/path."""
        # Arrange: Create PDF with spaces in name
        pdf_file = tmp_path / "my test file.pdf"
        pdf_file.write_bytes(b"%PDF-1.4\n")

        # Act & Assert
        from pdf_to_excel.utils import validate_pdf_file

        result = validate_pdf_file(str(pdf_file))
        assert result is True
