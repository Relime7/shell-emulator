@echo off
rem Stage 1: REPL, quotes, errors, exit. Input comes from text files (stdin redirect).
chcp 65001 >nul
set PYTHONUTF8=1
set PYTHONIOENCODING=utf-8
cd /d "%~dp0..\.."
if not defined PY set PY=python

echo.
echo ===== Stage 1: dialog (quotes, parse errors, unknown command) =====
%PY% main.py < scripts\os\input_stage1_a.txt
echo [exit code: %errorlevel%]

echo.
echo ===== Stage 1: empty lines, comments, exit with code =====
%PY% main.py < scripts\os\input_stage1_b.txt
echo [exit code: %errorlevel%]

echo.
echo ===== Stage 1: end of input (Ctrl+Z / EOF) =====
%PY% main.py < scripts\os\input_stage1_c.txt
echo [exit code: %errorlevel%]

echo.
echo ===== Stage 1: exit with bad argument =====
%PY% main.py < scripts\os\input_stage1_d.txt
echo [exit code: %errorlevel%]
exit /b 0
