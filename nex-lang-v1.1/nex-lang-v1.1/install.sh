#!/bin/bash
set -e

echo "=========================================="
echo "   NEX Language Installer v1.1"
echo "   Supports .N files and VS Code Extension"
echo "=========================================="

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "INFO: Installing from: $SCRIPT_DIR"

# Install Python package
python3 -m pip install -e "$SCRIPT_DIR"
echo "OK: Python package installed"

# Install VS Code Extension
VSCODE_EXT="$HOME/.vscode/extensions/nex-lang"
rm -rf "$VSCODE_EXT"
cp -r "$SCRIPT_DIR/vscode-extension" "$VSCODE_EXT"
echo "OK: VS Code Extension installed to: $VSCODE_EXT"

# Make nex executable
NEX_BIN="$(python3 -c 'import shutil, sys; print(shutil.which("nex") or "")')"
if [ -n "$NEX_BIN" ]; then
    chmod +x "$NEX_BIN" 2>/dev/null || true
fi

echo ""
echo "=========================================="
echo "Installation Complete!"
echo ""
echo "You can now use:"
echo "  nex hello.N"
echo "  nex --test"
echo "  nex install"
echo "  nex --help"
echo ""
echo "Please RESTART VS Code to see .N highlighting"
echo "=========================================="
