@echo off
setlocal

cd /d "%~dp0"

echo Starting FasalSathi...
echo.

call "%~dp0setup-and-run.bat"

if errorlevel 1 (
    echo.
    echo ERROR: FasalSathi failed to start.
    pause
    exit /b 1
)

exit /b 0
