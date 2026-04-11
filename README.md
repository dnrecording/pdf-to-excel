# PDF to Excel Converter

Convert scanned PDF tables to Excel with Thai/English language support using OCR.

## ✨ Features

- 🔍 **OCR Extraction**: Extract tables from scanned/image-based PDFs
- 🌏 **Thai Language**: Optimized for Thai (ภาษาไทย) and English text
- 📊 **Excel Output**: Generate formatted `.xlsx` files with Thai fonts
- 🖥️ **Easy GUI**: Simple drag-and-drop interface for non-technical users
- ⚡ **Simple CLI**: One command to convert PDF → Excel

## 🚀 Quick Start (No Installation Required!)

### Download Pre-Built App

**📦 [Download Latest Release](https://github.com/YOUR_USERNAME/pdf-to-excel/releases/latest)**

**macOS:**
1. Download `PDF-to-Excel-Converter-macOS.zip`
2. Unzip and drag to Applications folder
3. Right-click → Open (first time only)
4. Done! Just click to convert PDFs

**Windows:**
1. Download `PDF-to-Excel-Converter-Windows.zip`
2. Extract the folder anywhere
3. Double-click `PDF to Excel Converter.exe`
4. Click "Run anyway" if Windows asks (first time only)
5. Done! Just click to convert PDFs

**No Python, no Tesseract, no command line needed!**

> 💡 **First release coming soon!** After pushing to GitHub, create a release and the apps will build automatically.

---

## 🛠️ For Developers (Run from Source)

If you want to run from source code or contribute:

### Step 1: Install Tesseract OCR

**macOS:**
```bash
brew install tesseract tesseract-lang
```

**Windows:**
1. Download installer from: https://github.com/UB-Mannheim/tesseract/wiki
2. Run the installer (check "Additional language data" for Thai)

**Linux (Ubuntu/Debian):**
```bash
sudo apt-get install tesseract-ocr tesseract-ocr-tha
```

### Step 2: Install Python Packages

```bash
pip install -r requirements.txt
```

### Step 3: Run from Source

```bash
python gui_launcher.py
```

### Step 4: Build Standalone App (Optional)

To create your own standalone application:

**macOS:**
```bash
pip install -r requirements-build.txt
./build_app.sh
```

**Windows:**
```bash
pip install -r requirements-build.txt
build_app.bat
```

The built app will be in the `dist/` folder.

## 📖 Advanced Usage

### CLI (For automation/scripting)

```bash
# Basic conversion
python pdf-to-excel.py input.pdf output.xlsx

# With verbose output
python pdf-to-excel.py invoice.pdf result.xlsx --verbose

# English only
python pdf-to-excel.py doc.pdf output.xlsx --lang eng
```

## 💡 Tips for Best Results

- **Scan at 300+ DPI** for source PDFs
- **High contrast** documents work best
- **Manual review recommended** - OCR is not 100% perfect

## 🔧 Troubleshooting

### No Thai language pack
```bash
brew install tesseract-lang
tesseract --list-langs  # Should show 'tha'
```

### Poor OCR accuracy
- Check source PDF quality
- Consider re-scanning at higher resolution
- Low-quality PDFs will have OCR errors

## 📋 Development

For developers who want to contribute or modify the code:

```bash
make gui       # Launch GUI application
make test      # Run all 40 tests
make coverage  # Run tests with coverage report
make format    # Format code with black
make lint      # Check code style
make clean     # Remove generated files
```

### Test Coverage

- ✅ 40 tests passing
- 📄 Unit tests for PDF validation, OCR extraction, Excel writing
- 🖥️ GUI tests for button behavior, file browsing, state management
- 🔧 Mock-based testing for UI interactions
