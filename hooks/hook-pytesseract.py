"""
PyInstaller runtime hook for pytesseract and pdf2image

This hook configures pytesseract to use the bundled Tesseract binary
and tessdata directory, and configures pdf2image to use bundled Poppler
when running as a packaged application.
"""

import os
import sys
import pytesseract

# Get the directory where the bundled resources are located
if getattr(sys, 'frozen', False):
    # Running as bundled app
    bundle_dir = sys._MEIPASS

    # Set Tesseract command path
    tesseract_cmd = os.path.join(bundle_dir, 'tesseract', 'bin', 'tesseract')
    if sys.platform == 'win32':
        tesseract_cmd += '.exe'

    pytesseract.pytesseract.tesseract_cmd = tesseract_cmd

    # Set tessdata directory
    tessdata_dir = os.path.join(bundle_dir, 'tesseract', 'tessdata')
    os.environ['TESSDATA_PREFIX'] = tessdata_dir

    print(f"Configured Tesseract: {tesseract_cmd}")
    print(f"Tessdata directory: {tessdata_dir}")

    # Configure Poppler for pdf2image (all platforms)
    poppler_path = os.path.join(bundle_dir, 'poppler', 'bin')
    if os.path.exists(poppler_path):
        # Add poppler to PATH so pdf2image can find it
        os.environ['PATH'] = poppler_path + os.pathsep + os.environ.get('PATH', '')
        print(f"Configured Poppler: {poppler_path}")
