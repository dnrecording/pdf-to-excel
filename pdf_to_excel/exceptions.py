"""Custom exceptions for PDF to Excel converter."""


class PDFToExcelError(Exception):
    """Base exception for all package errors."""

    pass


class FileValidationError(PDFToExcelError):
    """Raised when file validation fails."""

    pass


class InvalidFileFormatError(FileValidationError):
    """Raised for non-PDF files or invalid format."""

    pass


class CorruptPDFError(FileValidationError):
    """Raised for corrupted PDF files."""

    pass


class ExtractionError(PDFToExcelError):
    """Raised when table extraction fails."""

    pass


class ProcessingError(PDFToExcelError):
    """Raised during data processing."""

    pass


class WriterError(PDFToExcelError):
    """Raised during Excel writing."""

    pass
