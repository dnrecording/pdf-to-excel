@echo off
REM Build script for PDF to Excel Converter (Windows)
REM Creates a standalone executable for Windows

echo 🚀 Building PDF to Excel Converter...

REM Check if pyinstaller is installed
pyinstaller --version >nul 2>&1
if %errorlevel% neq 0 (
    echo 📦 Installing build dependencies...
    pip install -r requirements-build.txt
)

REM Clean previous builds
echo 🧹 Cleaning previous builds...
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist

REM Run PyInstaller
echo 📦 Packaging application...
pyinstaller pdf-to-excel.spec

REM Check if build was successful
if exist "dist\PDF to Excel Converter\PDF to Excel Converter.exe" (
    echo.
    echo ✅ Build successful!
    echo.
    echo 📂 Application location:
    echo    dist\PDF to Excel Converter\
    echo.
    echo 🎯 To use:
    echo    1. Copy the entire "PDF to Excel Converter" folder to desired location
    echo    2. Double-click "PDF to Excel Converter.exe" to run
    echo.
    echo ⚠️  Windows may show a security warning on first run
    echo    Click "More info" → "Run anyway"
    echo.
) else (
    echo.
    echo ❌ Build failed!
    echo Check the output above for errors
    exit /b 1
)
