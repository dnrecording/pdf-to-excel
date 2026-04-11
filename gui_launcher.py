#!/usr/bin/env python
"""Launcher script for PDF to Excel GUI application."""

import sys
from pdf_to_excel.gui import main

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nApplication closed by user")
        sys.exit(0)
    except Exception as e:
        print(f"\nError starting application: {e}")
        sys.exit(1)
