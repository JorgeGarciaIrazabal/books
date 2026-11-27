@echo off
setlocal
echo Installing Book Studio Desktop for Windows...
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0install-windows.ps1"
if errorlevel 1 (
  echo.
  echo Installation failed. See message above.
  pause
  exit /b 1
)
echo.
pause
