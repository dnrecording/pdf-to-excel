# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec file for PDF to Excel Converter

This bundles the GUI application with all dependencies including:
- Python runtime
- All Python packages
- Tesseract OCR binary
- Thai and English language data
"""

import os
import sys
from pathlib import Path

block_cipher = None

# Determine Tesseract and Poppler paths
if sys.platform == 'darwin':  # macOS
    TESSERACT_BIN = '/opt/homebrew/bin/tesseract'
    TESSDATA_DIR = '/opt/homebrew/share/tessdata'
    # Poppler binaries on macOS (Homebrew)
    POPPLER_DIR = '/opt/homebrew/bin'
    POPPLER_BINS = ['pdftoppm', 'pdftocairo', 'pdfinfo']
elif sys.platform == 'win32':  # Windows
    TESSERACT_BIN = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
    TESSDATA_DIR = r'C:\Program Files\Tesseract-OCR\tessdata'
    POPPLER_DIR = r'C:\poppler\Library\bin'  # Poppler binaries for Windows
    POPPLER_BINS = None  # Bundle all .exe and .dll files
else:  # Linux
    TESSERACT_BIN = '/usr/bin/tesseract'
    TESSDATA_DIR = '/usr/share/tesseract-ocr/4.00/tessdata'
    POPPLER_DIR = '/usr/bin'
    POPPLER_BINS = ['pdftoppm', 'pdftocairo', 'pdfinfo']

# Data files to bundle
datas = []

# Bundle Tesseract binary
if os.path.exists(TESSERACT_BIN):
    datas.append((TESSERACT_BIN, 'tesseract/bin'))

# Bundle Thai and English language data
if os.path.exists(TESSDATA_DIR):
    # Resolve symlinks and copy actual files
    for lang in ['tha', 'eng']:
        lang_file = os.path.join(TESSDATA_DIR, f'{lang}.traineddata')
        if os.path.exists(lang_file):
            # If it's a symlink, resolve it
            if os.path.islink(lang_file):
                real_path = os.path.realpath(lang_file)
                datas.append((real_path, 'tesseract/tessdata'))
            else:
                datas.append((lang_file, 'tesseract/tessdata'))

# Bundle Poppler binaries
if POPPLER_DIR and os.path.exists(POPPLER_DIR):
    if POPPLER_BINS:
        # macOS/Linux: bundle specific binaries
        for bin_name in POPPLER_BINS:
            bin_path = os.path.join(POPPLER_DIR, bin_name)
            if os.path.exists(bin_path):
                datas.append((bin_path, 'poppler/bin'))
    else:
        # Windows: bundle all .exe and .dll files
        for file in os.listdir(POPPLER_DIR):
            if file.endswith(('.exe', '.dll')):
                file_path = os.path.join(POPPLER_DIR, file)
                datas.append((file_path, 'poppler/bin'))

# Hidden imports that PyInstaller might miss
hiddenimports = [
    'pdf_to_excel.gui',
    'pdf_to_excel.cli',
    'pdf_to_excel.extractor',
    'pdf_to_excel.writer',
    'pdf_to_excel.utils',
    'pdf_to_excel.exceptions',
    'PIL._tkinter_finder',
]

a = Analysis(
    ['gui_launcher.py'],
    pathex=[],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=['hooks'],
    hooksconfig={},
    runtime_hooks=['hooks/hook-pytesseract.py'],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='PDF to Excel Converter',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,  # No console window
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='PDF to Excel Converter',
)

# macOS: Create .app bundle
if sys.platform == 'darwin':
    app = BUNDLE(
        coll,
        name='PDF to Excel Converter.app',
        icon=None,  # TODO: Add icon file
        bundle_identifier='com.pdftoexcel.converter',
        info_plist={
            'NSHighResolutionCapable': 'True',
            'CFBundleShortVersionString': '1.0.0',
            'CFBundleVersion': '1.0.0',
            'NSHumanReadableCopyright': 'PDF to Excel Converter',
        },
    )
