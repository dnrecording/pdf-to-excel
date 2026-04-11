#!/bin/bash
# Build script for PDF to Excel Converter
# Creates a standalone application bundle for macOS

set -e  # Exit on error

echo "🚀 Building PDF to Excel Converter..."

# Check if pyinstaller is installed
if ! command -v pyinstaller &> /dev/null; then
    echo "📦 Installing build dependencies..."
    pip install -r requirements-build.txt
fi

# Clean previous builds
echo "🧹 Cleaning previous builds..."
rm -rf build dist "PDF to Excel Converter.app"

# Run PyInstaller
echo "📦 Packaging application..."
pyinstaller pdf-to-excel.spec

# Check if build was successful
if [ -d "dist/PDF to Excel Converter.app" ]; then
    echo ""
    echo "✅ Build successful!"
    echo ""
    echo "📂 Application location:"
    echo "   dist/PDF to Excel Converter.app"
    echo ""
    echo "🎯 To install:"
    echo "   1. Open Finder"
    echo "   2. Drag 'PDF to Excel Converter.app' to Applications folder"
    echo "   3. Double-click to run"
    echo ""
    echo "⚠️  First run: Right-click → Open (to bypass macOS security)"
    echo ""

    # Get app size
    APP_SIZE=$(du -sh "dist/PDF to Excel Converter.app" | cut -f1)
    echo "📊 Application size: $APP_SIZE"
else
    echo ""
    echo "❌ Build failed!"
    echo "Check the output above for errors"
    exit 1
fi
