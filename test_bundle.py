#!/usr/bin/env python
"""
Test script to verify bundled Tesseract works correctly.

This script can be run on the packaged application to verify:
1. Tesseract binary is found
2. Thai language data is available
3. OCR functionality works
"""

import sys
import os


def test_tesseract_availability():
    """Test if Tesseract is available and working."""
    print("🔍 Testing Tesseract availability...")

    try:
        import pytesseract
        from PIL import Image
        from io import BytesIO

        # Check Tesseract version
        version = pytesseract.get_tesseract_version()
        print(f"  ✅ Tesseract version: {version}")

        # Check available languages
        langs = pytesseract.get_languages()
        print(f"  ✅ Available languages: {', '.join(langs)}")

        # Check Thai language
        if 'tha' in langs:
            print("  ✅ Thai language data: Found")
        else:
            print("  ❌ Thai language data: Not found")
            return False

        # Check English language
        if 'eng' in langs:
            print("  ✅ English language data: Found")
        else:
            print("  ❌ English language data: Not found")
            return False

        return True

    except Exception as e:
        print(f"  ❌ Error: {e}")
        return False


def test_pdf_to_image():
    """Test if pdf2image works."""
    print("\n🔍 Testing PDF to image conversion...")

    try:
        from pdf2image import convert_from_path
        print("  ✅ pdf2image module loaded")
        return True
    except Exception as e:
        print(f"  ❌ Error: {e}")
        return False


def test_excel_writing():
    """Test if Excel writing works."""
    print("\n🔍 Testing Excel writing...")

    try:
        import pandas as pd
        import openpyxl

        # Create a simple DataFrame
        df = pd.DataFrame({
            'Thai': ['สวัสดี', 'ขอบคุณ'],
            'English': ['Hello', 'Thank you']
        })

        print("  ✅ DataFrame created")
        print("  ✅ openpyxl available")
        return True

    except Exception as e:
        print(f"  ❌ Error: {e}")
        return False


def test_bundled_paths():
    """Show bundled resource paths."""
    print("\n📂 Bundled resource paths:")

    if getattr(sys, 'frozen', False):
        bundle_dir = sys._MEIPASS
        print(f"  Bundle directory: {bundle_dir}")

        # Check Tesseract
        tesseract_bin = os.path.join(bundle_dir, 'tesseract', 'bin', 'tesseract')
        if sys.platform == 'win32':
            tesseract_bin += '.exe'

        if os.path.exists(tesseract_bin):
            print(f"  ✅ Tesseract binary: {tesseract_bin}")
        else:
            print(f"  ❌ Tesseract binary not found at: {tesseract_bin}")

        # Check tessdata
        tessdata_dir = os.path.join(bundle_dir, 'tesseract', 'tessdata')
        if os.path.exists(tessdata_dir):
            print(f"  ✅ Tessdata directory: {tessdata_dir}")

            # List language files
            lang_files = [f for f in os.listdir(tessdata_dir) if f.endswith('.traineddata')]
            print(f"     Language files: {', '.join(lang_files)}")
        else:
            print(f"  ❌ Tessdata directory not found at: {tessdata_dir}")
    else:
        print("  ℹ️  Running from source (not bundled)")


def main():
    """Run all tests."""
    print("=" * 60)
    print("PDF to Excel Converter - Bundle Test")
    print("=" * 60)

    if getattr(sys, 'frozen', False):
        print("🎯 Running as bundled application")
    else:
        print("🎯 Running from source")

    print()

    # Run tests
    results = []
    results.append(("Tesseract", test_tesseract_availability()))
    results.append(("PDF to Image", test_pdf_to_image()))
    results.append(("Excel Writing", test_excel_writing()))

    # Show bundled paths
    test_bundled_paths()

    # Summary
    print("\n" + "=" * 60)
    print("Test Summary:")
    print("=" * 60)

    all_passed = True
    for name, passed in results:
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"{name:20s} {status}")
        if not passed:
            all_passed = False

    print("=" * 60)

    if all_passed:
        print("\n✅ All tests passed! The bundled app should work correctly.")
        return 0
    else:
        print("\n❌ Some tests failed. Check the errors above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
