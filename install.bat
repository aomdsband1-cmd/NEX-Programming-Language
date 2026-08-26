@echo off
chcp 65001 >nul
echo ==========================================
echo    NEX Language Installer v1.1
echo    Supports .N files and VS Code Extension
echo ==========================================
echo.
echo TIP: PowerShell run: .\install.bat
echo TIP: CMD run: install.bat
echo.

set SCRIPT_DIR=%~dp0
REM Remove trailing backslash to fix quote escaping bug
if "%SCRIPT_DIR:~-1%"=="\" set SCRIPT_DIR=%SCRIPT_DIR:~0,-1%

echo INFO: Installing from: %SCRIPT_DIR%

REM Install Python package
python -m pip install -e "%SCRIPT_DIR%"
if errorlevel 1 (
    echo WARN: pip install failed. Make sure Python is installed and in PATH.
    pause
    exit /b 1
)
echo OK: Python package installed

REM Install VS Code Extension
set VSCODE_EXT=%USERPROFILE%\.vscode\extensions\nex-lang
if exist "%VSCODE_EXT%" rmdir /S /Q "%VSCODE_EXT%"
xcopy /E /I /Y "%SCRIPT_DIR%\vscode-extension" "%VSCODE_EXT%"
echo OK: VS Code Extension installed

REM Add Scripts to PATH
for /f "tokens=*" %%a in ('python -c "import sys; print(sys.executable)"') do set PYTHON_EXE=%%a
for %%F in ("%PYTHON_EXE%") do set PYTHON_DIR=%%~dpF
set SCRIPTS_DIR=%PYTHON_DIR%Scripts
powershell -Command "$p=[Environment]::GetEnvironmentVariable('Path','User'); if($p -notlike '*%SCRIPTS_DIR%*'){ [Environment]::SetEnvironmentVariable('Path',$p+';%SCRIPTS_DIR%','User'); echo 'OK: Added to PATH' } else { echo 'OK: Already in PATH' }"

REM Register .N file association
reg add "HKCU\Software\Classes\.N" /ve /t REG_SZ /d "NEXSourceFile" /f >nul 2>&1
reg add "HKCU\Software\Classes\NEXSourceFile" /ve /t REG_SZ /d "NEX Source File" /f >nul 2>&1
reg add "HKCU\Software\Classes\NEXSourceFile\shell\open\command" /ve /t REG_SZ /d "\"nex\" \"%1\"" /f >nul 2>&1
echo OK: Registered .N file association

echo.
echo ==========================================
echo Installation Complete!
echo.
echo You can now use:
echo   nex hello.N
echo   nex --test
echo   nex install
echo   nex --help
echo.
echo Please RESTART VS Code to see .N highlighting
echo Please RESTART PowerShell/CMD to use nex command
echo ==========================================
pause
