@echo off
echo ==========================================
echo    NEX Standalone Executable Builder
echo ==========================================
echo.

REM Check if pyinstaller is installed
python -c "import PyInstaller" 2>nul
if errorlevel 1 (
    echo Installing PyInstaller...
    python -m pip install pyinstaller
)

echo Building standalone executable...
pyinstaller --onefile --name nex --icon=assets\icon.ico interpreter.py

if errorlevel 1 (
    echo [ERROR] Build failed.
    pause
    exit /b 1
)

echo.
echo [OK] Build complete!
echo Executable: dist\nex.exe
echo.
echo You can now run: dist\nex.exe hello.N
pause
