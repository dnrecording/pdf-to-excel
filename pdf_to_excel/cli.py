"""Command-line interface for PDF to Excel converter."""

import argparse
import sys
from pathlib import Path

from .extractor import OCRExtractor, pdf_needs_ocr
from .utils import validate_pdf_file
from .writer import ExcelWriter
from .exceptions import PDFToExcelError


def main() -> int:
    """
    Main entry point for CLI.

    Returns:
        Exit code (0 for success, 1 for error)
    """
    parser = argparse.ArgumentParser(
        description="Convert PDF tables to Excel with Thai language support",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s input.pdf output.xlsx
  %(prog)s scanned.pdf result.xlsx --verbose
  %(prog)s thai_invoice.pdf invoice.xlsx --lang tha eng

  # Try different OCR engines for better accuracy:
  %(prog)s low_quality.pdf output.xlsx --ocr-mode 1 --psm 3
  %(prog)s sparse_text.pdf output.xlsx --psm 11

OCR Engine Modes (--ocr-mode):
  0: Legacy engine (old, sometimes better for low quality)
  1: LSTM neural network (best for most cases)
  2: Legacy + LSTM combined
  3: Default (automatic selection)

Page Segmentation Modes (--psm):
  3: Fully automatic (good for complex layouts)
  4: Single column of text
  6: Uniform block (default, good for tables)
  11: Sparse text (good for scattered text)
  12: Sparse text with orientation detection

Supported languages: tha (Thai), eng (English)
        """,
    )

    parser.add_argument("input_pdf", help="Input PDF file path")
    parser.add_argument("output_excel", help="Output Excel file path")
    parser.add_argument(
        "--lang",
        nargs="+",
        default=["tha", "eng"],
        help="OCR languages (default: tha eng)",
    )
    parser.add_argument(
        "-v", "--verbose", action="store_true", help="Verbose output"
    )
    parser.add_argument(
        "--ocr-mode",
        type=int,
        choices=[0, 1, 2, 3],
        default=3,
        help="Tesseract OCR Engine Mode: 0=Legacy, 1=LSTM, 2=Legacy+LSTM, 3=Default (default: 3)",
    )
    parser.add_argument(
        "--psm",
        type=int,
        choices=[3, 4, 6, 11, 12],
        default=6,
        help="Page Segmentation Mode: 3=Auto, 4=Single column, 6=Uniform block, 11=Sparse text, 12=Sparse+OSD (default: 6)",
    )

    args = parser.parse_args()

    try:
        # Validate input
        print(f"📄 Input PDF: {args.input_pdf}")
        validate_pdf_file(args.input_pdf)

        # Check PDF type
        if args.verbose:
            print("\n🔍 Detecting PDF type...")
        needs_ocr = pdf_needs_ocr(args.input_pdf)

        if needs_ocr:
            print("   → Scanned/Image-based PDF (will use OCR)")
        else:
            print("   → Native PDF with text (will use OCR anyway for consistency)")

        # Extract with OCR
        print(f"\n🔎 Extracting tables (Languages: {', '.join(args.lang)})...")
        if args.verbose:
            print(f"   OCR Engine Mode: {args.ocr_mode}, Page Segmentation: {args.psm}")

        # Use default settings optimized for each language
        extractor = OCRExtractor(
            languages=args.lang, ocr_mode=args.ocr_mode, psm_mode=args.psm
        )

        # Extract tables (includes OCR, parsing, and post-processing)
        print("📊 Parsing table structure...")
        tables = extractor.extract_tables_from_pdf(args.input_pdf)

        if not tables or len(tables) == 0:
            print("❌ No table structure detected in PDF")
            print("   The PDF may not contain tabular data,")
            print("   or the OCR could not identify clear columns.")
            return 1

        # Use first table
        table_data = tables[0]

        if args.verbose:
            print(f"   → Found table with {len(table_data)} rows, {len(table_data[0]) if table_data else 0} columns")

        # Write to Excel
        print(f"\n💾 Writing to Excel: {args.output_excel}")
        writer = ExcelWriter()
        writer.write_table_to_excel(
            table_data,
            args.output_excel,
            apply_formatting=True,
        )

        print("   → Applied formatting (Thai font, headers, etc.)")
        print("\n✅ Conversion complete!")
        print(f"   Output: {args.output_excel}")

        return 0

    except PDFToExcelError as e:
        print(f"\n❌ Error: {e}", file=sys.stderr)
        if args.verbose:
            import traceback

            traceback.print_exc()
        return 1
    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupted by user")
        return 130
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}", file=sys.stderr)
        if args.verbose:
            import traceback

            traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
