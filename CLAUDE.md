# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

PDF to Excel converter with **Thai/English language support** using **OCR** (Optical Character Recognition). Designed specifically for scanned documents where native PDF text extraction doesn't work.

**Critical Context:** This project was built using **Test-Driven Development (TDD)** with 40 passing tests.

## Key Commands

### Development
```bash
make gui       # Launch GUI application (primary interface)
make test      # Run all 40 tests
make coverage  # Run tests with coverage report
make format    # Format code with black
make lint      # Check code style with flake8
make clean     # Remove generated files

# Run specific test
source .venv/bin/activate && pytest tests/unit/test_gui.py::TestPDFToExcelGUI::test_convert_button_click -xvs

# Run CLI directly
python pdf-to-excel.py input.pdf output.xlsx --verbose
```

### Building Standalone Applications
```bash
# Build for current platform (macOS/Windows)
./build_app.sh      # macOS
build_app.bat       # Windows

# Test bundled app
python test_bundle.py

# Build artifacts location
open "dist/PDF to Excel Converter.app"          # macOS
"dist\PDF to Excel Converter\PDF to Excel Converter.exe"  # Windows
```

### Setup
```bash
# Install dependencies
pip install -r requirements.txt

# Install Tesseract OCR (macOS)
brew install tesseract tesseract-lang

# Verify Thai language pack
tesseract --list-langs | grep tha
```

## Architecture

### Core Components

**OCR-Based Pipeline:**
```
PDF → pdf2image → Tesseract OCR → Table Parser → Excel Writer
```

1. **extractor.py** (`OCRExtractor`):
   - Converts PDF pages to images (300 DPI) using pdf2image
   - **Critical:** Explicitly passes poppler_path to convert_from_path when running as bundled app
   - Runs Tesseract OCR with Thai+English
   - Parses table structure from OCR text using regex (splits on 2+ spaces/tabs)
   - **Critical:** Uses OCR mode 3 (default) and PSM mode 6 (table)
   - **No image preprocessing** - raw images work best for Thai (preprocessing destroyed tone marks)

2. **writer.py** (`ExcelWriter`):
   - Writes to Excel with openpyxl
   - Applies Thai font (TH SarabunPSK, 16pt)
   - **Handles variable column counts** by padding rows to max_cols
   - Auto-adjusts column widths (Thai chars count as 1.5x wider)

3. **gui.py** (`PDFToExcelGUI`):
   - Tkinter-based Nord dark theme UI
   - Custom `ModernButton` canvas widget with hover effects
   - Drop zone for file selection (click anywhere to browse)
   - Background threading prevents UI freezing during OCR
   - **Debouncing:** `is_browsing` flag prevents multiple concurrent file dialogs

4. **cli.py**:
   - Simplified CLI with essential flags: `--lang`, `--verbose`, `--ocr-mode`, `--psm`
   - Removed: `--high-quality`, `--no-enhance`, `--no-format` (not needed)

5. **exceptions.py**:
   - Exception hierarchy: `PDFToExcelError` → `FileValidationError`, `ExtractionError`, `WriterError`

### Design Decisions & Lessons Learned

**Thai Language Support:**
- **DO NOT** use image preprocessing (contrast/binarization) - it destroys Thai tone marks
- Raw 300 DPI images work best
- Thai Unicode range: `\u0E00` to `\u0E7F`
- Thai fonts need 1.5x width multiplier in Excel

**OCR Configuration:**
- Default settings work best: `--oem 3 --psm 6`
- Multiple attempts to improve with different modes didn't help quality
- Simple table parsing (split on 2+ spaces) is sufficient

**GUI Architecture:**
- Use `root.after()` for cross-thread communication (OCR runs in background thread)
- Reset all flags in `finally` blocks to prevent stuck states
- `is_browsing` debouncing prevents rapid-click issues
- Canvas-based buttons for rounded corners and hover effects

**Testing:**
- 40 tests: 25 GUI tests + 15 extractor/writer/utils tests
- GUI tests use mocks for file dialogs and threading
- All tkinter widgets created in fixtures must be destroyed in teardown

## File Structure

```
pdf_to_excel/
├── __init__.py
├── __main__.py         # Entry point for python -m
├── cli.py             # Command-line interface
├── extractor.py       # OCR extraction (OCRExtractor class)
├── writer.py          # Excel writing (ExcelWriter class)
├── gui.py             # GUI app (PDFToExcelGUI, ModernButton)
├── utils.py           # PDF validation helpers
└── exceptions.py      # Custom exception hierarchy

tests/
├── conftest.py        # Shared fixtures (sample_thai_dataframe)
├── unit/
│   ├── test_utils.py       # 5 tests
│   ├── test_extractor.py   # 10 tests
│   ├── test_writer.py      # (not yet created)
│   └── test_gui.py         # 25 tests
└── integration/       # (placeholder)

gui_launcher.py        # GUI entry point
pdf-to-excel.py        # CLI entry point
pdf-to-excel.spec      # PyInstaller configuration
build_app.sh           # macOS build script
build_app.bat          # Windows build script
test_bundle.py         # Bundle verification script
hooks/
└── hook-pytesseract.py  # PyInstaller runtime hook

.github/workflows/
└── build-release.yml   # Automated cross-platform builds
```

## Critical Implementation Notes

### Thai Text Handling
```python
# ✅ DO: Use raw images
images = convert_from_path(pdf_path, dpi=300, fmt='png')
text = pytesseract.image_to_string(image, lang='tha+eng', config='--oem 3 --psm 6')

# ❌ DON'T: Preprocess images
# Binarization/contrast enhancement destroys Thai tone marks
```

### Variable Column Counts
```python
# Excel writer must pad rows to match max column count
max_cols = max(len(row) for row in table_data)
padded_data = [row + [''] * (max_cols - len(row)) for row in table_data]
df = pd.DataFrame(padded_data[1:], columns=padded_data[0])
```

### GUI Thread Safety
```python
# ✅ DO: Use root.after() for cross-thread UI updates
def _do_conversion(self, pdf_path, output_path):
    try:
        # ... OCR work in background thread ...
        self.root.after(0, self._update_status, "Processing...", color)
    finally:
        self.root.after(0, self._set_converting, False)
```

### Debouncing File Dialogs
```python
def _browse_file(self):
    if self.is_browsing:
        return  # Prevent multiple dialogs

    self.is_browsing = True
    try:
        file_path = filedialog.askopenfilename(...)
    finally:
        self.is_browsing = False  # Always reset in finally
```

## Dependencies

**OCR Stack:**
- `pytesseract` - Python wrapper for Tesseract
- `pdf2image` - Convert PDF to images
- `Pillow` - Image handling
- `PyPDF2` - PDF validation

**Data Processing:**
- `pandas` - DataFrame operations
- `openpyxl` - Excel file generation

**System Requirements (for development):**
- Tesseract OCR with Thai language pack (`tesseract-lang`)
- Poppler (for pdf2image):
  - macOS: `brew install poppler`
  - Windows: Install from poppler-windows releases or via package manager
  - Linux: `sudo apt-get install poppler-utils`

**Standalone app (end users):**
- Both Tesseract and Poppler are bundled - no installation required

## Common Issues & Solutions

**Issue:** OCR results have garbled Thai text
- **Cause:** Image preprocessing was applied
- **Fix:** Use raw images at 300 DPI, no preprocessing

**Issue:** Excel has misaligned columns
- **Cause:** Variable column counts from OCR
- **Fix:** Pad all rows to `max_cols` before creating DataFrame

**Issue:** File browser won't open after canceling
- **Cause:** `is_browsing` flag stuck
- **Fix:** Always reset flags in `finally` blocks

**Issue:** GUI freezes during conversion
- **Cause:** OCR running in main thread
- **Fix:** Use `threading.Thread` with `root.after()` for UI updates

**Issue:** Bundled app can't find Tesseract
- **Cause:** Tesseract paths not configured for frozen app
- **Fix:** Use runtime hook to set paths from `sys._MEIPASS`

**Issue:** GitHub Actions build fails on Windows
- **Cause:** Tesseract installation failed
- **Fix:** Workflow uses Chocolatey package manager (reliable and pre-installed on GitHub Actions runners). If Thai language download fails, update tessdata URL in workflow.

**Issue:** App fails with "Unable to get page count. Is poppler installed?" (both macOS and Windows)
- **Cause:** Poppler binaries not bundled correctly or not found in bundled app
- **Fix:**
  - **CRITICAL**: Poppler files must be in `binaries` list, not `datas` (maintains executable permissions and DLL loading)
  - Spec file bundles poppler binaries for all platforms
  - Runtime hook adds poppler to PATH
  - Extractor explicitly passes poppler_path to convert_from_path when running as frozen app
  - Workflow installs poppler on both macOS and Windows
  - Added debug output to diagnose bundling issues

## Testing Strategy

**Unit Tests:**
- Mock file system operations with `patch`
- Mock tkinter dialogs: `filedialog.askopenfilename`, `messagebox.showerror`
- Test button clicks with `btn._on_click(Mock())`
- Verify state changes (flags, button text, colors)

**GUI Tests:**
- Create `root = tk.Tk()` in fixture, destroy in teardown
- Test threading without actually running threads (mock `threading.Thread`)
- Check debouncing by setting flags manually

**Integration Tests:**
- Test with real PDF files (not yet implemented)
- Verify end-to-end conversion accuracy

## Packaging & Distribution

### Standalone Application Architecture

The project packages as standalone applications that bundle:
- Python interpreter and all dependencies
- Tesseract OCR binary
- Thai and English language data files
- Poppler binaries (for PDF to image conversion - all platforms)
- Application code

**Platform-specific builds:**
- macOS: `.app` bundle (~150-200 MB installed)
- Windows: `.exe` with folder (~150-200 MB installed)
- Users need NO installation - just download and run

### PyInstaller Configuration

**pdf-to-excel.spec** defines what to bundle:

```python
if sys.platform == 'darwin':  # macOS
    TESSERACT_BIN = '/opt/homebrew/bin/tesseract'
    TESSDATA_DIR = '/opt/homebrew/share/tessdata'
    POPPLER_DIR = '/opt/homebrew/bin'
    POPPLER_BINS = ['pdftoppm', 'pdftocairo', 'pdfinfo']
elif sys.platform == 'win32':  # Windows
    TESSERACT_BIN = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
    TESSDATA_DIR = r'C:\Program Files\Tesseract-OCR\tessdata'
    POPPLER_DIR = r'C:\poppler\Library\bin'
    POPPLER_BINS = None  # Bundle all .exe and .dll files

datas = [
    (TESSDATA_DIR + '/tha.traineddata', 'tesseract/tessdata'),
    (TESSDATA_DIR + '/eng.traineddata', 'tesseract/tessdata'),
]

binaries = []

# Bundle Tesseract binary
if os.path.exists(TESSERACT_BIN):
    binaries.append((TESSERACT_BIN, 'tesseract/bin'))

# Bundle Poppler binaries (CRITICAL: must be in binaries, not datas)
if POPPLER_DIR and os.path.exists(POPPLER_DIR):
    if POPPLER_BINS:
        # macOS/Linux: bundle specific binaries
        for bin_name in POPPLER_BINS:
            bin_path = os.path.join(POPPLER_DIR, bin_name)
            if os.path.exists(bin_path):
                binaries.append((bin_path, 'poppler/bin'))
    else:
        # Windows: bundle all .exe and .dll files
        for file in os.listdir(POPPLER_DIR):
            if file.endswith(('.exe', '.dll')):
                binaries.append((os.path.join(POPPLER_DIR, file), 'poppler/bin'))
```

**hooks/hook-pytesseract.py** (runtime hook):

Configures Tesseract and Poppler paths when running as frozen/bundled app:

```python
if getattr(sys, 'frozen', False):
    bundle_dir = sys._MEIPASS

    # Configure Tesseract
    tesseract_cmd = os.path.join(bundle_dir, 'tesseract', 'bin', 'tesseract')
    pytesseract.pytesseract.tesseract_cmd = tesseract_cmd
    tessdata_dir = os.path.join(bundle_dir, 'tesseract', 'tessdata')
    os.environ['TESSDATA_PREFIX'] = tessdata_dir

    # Configure Poppler (all platforms)
    poppler_path = os.path.join(bundle_dir, 'poppler', 'bin')
    if os.path.exists(poppler_path):
        os.environ['PATH'] = poppler_path + os.pathsep + os.environ['PATH']
```

### Local Build Process

**macOS** (`build_app.sh`):
1. Checks Tesseract installation
2. Installs PyInstaller
3. Cleans previous builds
4. Runs `pyinstaller pdf-to-excel.spec`
5. Creates `.app` bundle in `dist/`

**Windows** (`build_app.bat`):
1. Same steps as macOS
2. Creates `.exe` with folder structure

**Verification** (`test_bundle.py`):
- Tests if Tesseract binary is found
- Verifies Thai/English language data availability
- Useful for debugging bundle issues
- Run after building to ensure everything works

### Automated Cross-Platform Builds (GitHub Actions)

**When triggered:** Creating a GitHub release or manual workflow dispatch

**What happens:**

`.github/workflows/build-release.yml` runs:

1. **macOS job** (runs on `macos-latest`):
   - Install Tesseract + Thai language + Poppler: `brew install tesseract tesseract-lang poppler`
   - Install Python dependencies
   - Run PyInstaller (bundles Tesseract and Poppler binaries)
   - Create `PDF-to-Excel-Converter-macOS.zip`
   - Upload to GitHub Release

2. **Windows job** (runs on `windows-latest`):
   - Install Tesseract via Chocolatey (reliable package manager)
   - Download Thai language data from tessdata repository
   - Download and extract Poppler for Windows
   - Install Python dependencies
   - Run PyInstaller (bundles Tesseract and Poppler)
   - Create `PDF-to-Excel-Converter-Windows.zip`
   - Upload to GitHub Release

3. **Summary job**:
   - Downloads both artifacts
   - Displays build completion status

**Build time:** ~15-20 minutes (both platforms run in parallel)

**Triggering builds:**

```bash
# Method 1: Create GitHub release (automatic)
# 1. Go to GitHub → Releases → "Draft a new release"
# 2. Create tag: v1.0.0
# 3. Publish release
# 4. Builds start automatically

# Method 2: Manual trigger from Actions tab
# 1. Go to Actions → "Build Standalone Applications"
# 2. Click "Run workflow"
# 3. Enter version tag
# 4. Builds start (artifacts only, not uploaded to release)
```

**Important:** PyInstaller builds are platform-specific. You MUST build on macOS for macOS, Windows for Windows. This is why GitHub Actions is essential - it provides both platforms without needing physical machines.

### Distribution Strategy

**GitHub Releases (recommended):**
- Upload platform-specific zips
- Automated via GitHub Actions
- Easy for users to find and download
- Permanent storage (until deleted)

**Release naming:**
- Tag: `v1.0.0` (semantic versioning)
- Files: `PDF-to-Excel-Converter-macOS.zip`, `PDF-to-Excel-Converter-Windows.zip`

**Download URLs format:**
```
https://github.com/USERNAME/pdf-to-excel/releases/download/v1.0.0/PDF-to-Excel-Converter-macOS.zip
https://github.com/USERNAME/pdf-to-excel/releases/latest  # Always latest release
```

### User Installation

**macOS:**
1. Download `PDF-to-Excel-Converter-macOS.zip`
2. Unzip and drag to Applications
3. Right-click → Open (first time only to bypass Gatekeeper)
4. Done - no dependencies needed

**Windows:**
1. Download `PDF-to-Excel-Converter-Windows.zip`
2. Extract folder anywhere
3. Run `PDF to Excel Converter.exe`
4. Click "Run anyway" if SmartScreen warning appears
5. Done - no dependencies needed

### Known Distribution Issues

**Security warnings:**
- macOS: "Unverified developer" (unsigned .app)
  - Solution: Right-click → Open, or code sign with Apple Developer cert ($99/year)
- Windows: SmartScreen "Unknown publisher" (unsigned .exe)
  - Solution: Click "More info" → "Run anyway", or code sign with cert (~$100-400/year)

**First launch delay:**
- Takes 5-10 seconds on first run (unpacking Tesseract)
- Normal behavior, not a bug

**Antivirus false positives:**
- Some AVs flag PyInstaller executables
- Solution: Code signing or submit for whitelisting

### Documentation for Packaging

- **BUILD.md**: Detailed local build instructions, troubleshooting
- **PACKAGING.md**: Overview of packaging system, bundle contents
- **RELEASE.md**: How to create releases with automated builds
- **GITHUB_SETUP.md**: First-time GitHub setup, enabling Actions, creating first release

## Version History Context

This project evolved through several iterations:
1. **Initial plan:** Use tabula-py (abandoned - can't handle scanned PDFs)
2. **OCR exploration:** Added Tesseract with Thai support
3. **Preprocessing experiment:** Tried image enhancement (abandoned - damaged Thai text)
4. **CLI simplification:** Removed unnecessary flags based on user feedback
5. **GUI development:** Built tkinter interface with Nord theme
6. **GUI refinement:** Simplified design based on user feedback (removed bottom text, simplified drop zone)
7. **Packaging:** Added PyInstaller configuration and build scripts for standalone apps
8. **CI/CD:** Implemented GitHub Actions for automated cross-platform builds
9. **Current:** Production-ready with automated distribution for both macOS and Windows

The `/spec` directory contains original design docs that don't fully match current implementation - refer to actual code as source of truth.
