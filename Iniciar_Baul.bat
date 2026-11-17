@echo off
setlocal
cd /d "%~dp0"
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0iniciar_baul.ps1"
set "RESULTADO=%ERRORLEVEL%"
if not "%RESULTADO%"=="0" (
  echo.
  echo Baul no pudo iniciarse. Lee el mensaje anterior.
  pause
)
exit /b %RESULTADO%
