@echo off
chcp 65001 >nul
setlocal
cd /d "%~dp0"
if not exist "%~dp0.venv\Scripts\python.exe" goto missing
"%~dp0.venv\Scripts\python.exe" "%~dp0main.py" %*
set "SPA_EXIT=%ERRORLEVEL%"
if "%SPA_EXIT%"=="0" exit /b 0
pause
exit /b %SPA_EXIT%
:missing
echo Сначала установите Python и зависимости по инструкции README.md.
echo Ожидается окружение .venv в папке приложения.
pause
exit /b 1
