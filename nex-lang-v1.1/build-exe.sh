#!/bin/bash
set -e

echo "=========================================="
echo "   NEX Standalone Executable Builder"
echo "=========================================="

# Check if pyinstaller is installed
if ! python -c "import PyInstaller" 2>/dev/null; then
    echo "Installing PyInstaller..."
    python3 -m pip install pyinstaller
fi

echo "Building standalone executable..."
pyinstaller --onefile --name nex --icon=assets/icon.png interpreter.py

echo ""
echo "[OK] Build complete!"
echo "Executable: dist/nex"
echo ""
echo "You can now run: ./dist/nex hello.N"
