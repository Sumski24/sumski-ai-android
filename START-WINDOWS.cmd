@echo off
setlocal
cd /d "%~dp0"
py -3 --version >nul 2>&1
if not errorlevel 1 (
  py -3 "%~dp0export_watch5.py" %*
  goto finish
)
python --version >nul 2>&1
if not errorlevel 1 (
  python "%~dp0export_watch5.py" %*
  goto finish
)
echo Python 3 was not found. Install it from https://www.python.org/downloads/
echo Then run this file again.
:finish
echo.
pause
