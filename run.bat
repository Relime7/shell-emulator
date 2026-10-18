@echo off
rem Run the emulator: run.bat [--vfs PATH] [--script PATH] [--config PATH]
rem Set PY to choose the interpreter (default: py -3, then python).
chcp 65001 >nul
set PYTHONUTF8=1
if defined PY (
  %PY% "%~dp0src\main.py" %*
  exit /b
)
where py >nul 2>nul
if %errorlevel%==0 (
  py -3 "%~dp0src\main.py" %*
) else (
  python "%~dp0src\main.py" %*
)
