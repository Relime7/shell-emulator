@echo off
rem Stage 3: different VFS variants (minimal, several files, 3+ levels) and load errors.
chcp 65001 >nul
set PYTHONUTF8=1
set PYTHONIOENCODING=utf-8
cd /d "%~dp0..\.."
if not defined PY set PY=python

call :section "Minimal VFS (empty root)"
call :run %PY% main.py --vfs vfs/minimal.json --script scripts/vfs_probe.emu
call :section "VFS with several files (text, base64 binary, hidden file, spaces in names)"
call :run %PY% main.py --vfs vfs/files.json --script scripts/vfs_probe.emu
call :section "VFS with 6 levels of nesting"
call :run %PY% main.py --vfs vfs/deep.json --script scripts/vfs_probe.emu
call :section "Error: VFS root is a file"
call :run %PY% main.py --vfs vfs/broken/root_is_file.json
call :section "Error: unknown node type"
call :run %PY% main.py --vfs vfs/broken/bad_type.json
call :section "Error: invalid base64"
call :run %PY% main.py --vfs vfs/broken/bad_base64.json
call :section "Error: invalid mode"
call :run %PY% main.py --vfs vfs/broken/bad_mode.json
call :section "Error: invalid JSON"
call :run %PY% main.py --vfs vfs/broken/invalid_json.json
call :section "Error: VFS file does not exist"
call :run %PY% main.py --vfs vfs/nope.json
call :section "Full test of all commands of all stages (deep.json)"
call :run %PY% main.py --vfs vfs/deep.json --script scripts/full_test.emu
exit /b 0

:section
echo.
echo ================================================================
echo == %~1
echo ================================================================
exit /b 0

:run
echo.
echo ^> %*
%* < NUL
echo [exit code: %errorlevel%]
exit /b 0
