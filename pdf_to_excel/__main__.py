"""Entry point for python -m pdf_to_excel."""

import sys
from .cli import main

if __name__ == "__main__":
    sys.exit(main())
