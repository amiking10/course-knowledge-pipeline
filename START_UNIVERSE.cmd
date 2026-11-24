@echo off
setlocal
cd /d "%~dp0"
where powershell.exe >nul 2>&1
if errorlevel 1 (
  echo UNI-VERSE needs Windows PowerShell. Open this file on Windows, not in Ubuntu/WSL.
  pause
  exit /b 1
)
powershell.exe -NoProfile -STA -File "%~dp0scripts\launcher_windows.ps1"
set "result=%ERRORLEVEL%"
if not "%result%"=="0" (
  echo.
  echo UNI-VERSE could not start or finish successfully.
  echo If Windows blocked the script, check the PowerShell policy guidance in README.md.
)
echo.
pause
exit /b %result%
