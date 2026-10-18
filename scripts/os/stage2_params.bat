@echo off
rem Stage 2: CLI parameters, JSON config, priorities, startup script.
chcp 65001 >nul
set PYTHONUTF8=1
set PYTHONIOENCODING=utf-8
cd /d "%~dp0..\.."
if not defined PY set PY=python

call :section "No parameters"
call :run %PY% main.py
call :section "Only --vfs"
call :run %PY% main.py --vfs vfs/files.json
call :section "Only --script"
call :run %PY% main.py --script scripts/hello.emu
call :section "Only --config (VFS and script come from the file)"
call :run %PY% main.py --config config/default.json
call :section "All three parameters"
call :run %PY% main.py --config config/default.json --vfs vfs/files.json --script scripts/hello.emu
call :section "Priority: CLI --vfs overrides config vfs_path"
call :run %PY% main.py --config config/default.json --vfs vfs/minimal.json
call :section "Priority: CLI --script overrides config script_path"
call :run %PY% main.py --config config/default.json --script scripts/stage1_parser.emu --vfs vfs/deep.json
call :section "Partial config (vfs only) + script from CLI"
call :run %PY% main.py --config config/only_vfs.json --script scripts/hello.emu
call :section "Partial config (script only) + VFS from CLI"
call :run %PY% main.py --config config/only_script.json --vfs vfs/files.json
call :section "Error: config file does not exist"
call :run %PY% main.py --config config/no_such.json
call :section "Error: invalid JSON in config"
call :run %PY% main.py --config config/broken.json
call :section "Error: wrong field type in config"
call :run %PY% main.py --config config/bad_types.json
call :section "Error: config points to missing VFS"
call :run %PY% main.py --config config/missing_vfs.json
call :section "Error: config points to missing script (emulator keeps running)"
call :run %PY% main.py --config config/missing_script.json
call :section "Error: unknown command-line option"
call :run %PY% main.py --unknown
call :section "Error: option without value"
call :run %PY% main.py --vfs
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
