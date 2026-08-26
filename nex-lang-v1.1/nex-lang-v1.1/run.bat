@echo off
if "%~1"=="" (
    echo Usage: run.bat [file.N or file.nex]
    exit /b 1
)
python interpreter.py %*
