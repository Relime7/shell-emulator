#!/usr/bin/env bash
# Этап 2: параметры командной строки, JSON-конфиг, приоритеты, стартовый скрипт.
source "$(dirname "$0")/common.sh"

section "Без параметров"
run $PY main.py

section "Только --vfs"
run $PY main.py --vfs vfs/files.json

section "Только --script"
run $PY main.py --script scripts/hello.emu

section "Только --config (VFS и скрипт берутся из файла)"
run $PY main.py --config config/default.json

section "Все три параметра"
run $PY main.py --config config/default.json --vfs vfs/files.json --script scripts/hello.emu

section "Приоритет: --vfs из CLI перекрывает vfs_path из конфига (minimal вместо files)"
run $PY main.py --config config/default.json --vfs vfs/minimal.json

section "Приоритет: --script из CLI перекрывает script_path из конфига"
run $PY main.py --config config/default.json --script scripts/stage1_parser.emu --vfs vfs/deep.json

section "Частичный конфиг (только vfs_path) + скрипт из CLI"
run $PY main.py --config config/only_vfs.json --script scripts/hello.emu

section "Частичный конфиг (только script_path) + VFS из CLI"
run $PY main.py --config config/only_script.json --vfs vfs/files.json

section "Ошибки: несуществующий конфиг"
run $PY main.py --config config/no_such.json

section "Ошибки: некорректный JSON в конфиге"
run $PY main.py --config config/broken.json

section "Ошибки: неверный тип поля в конфиге"
run $PY main.py --config config/bad_types.json

section "Ошибки: конфиг ссылается на несуществующую VFS"
run $PY main.py --config config/missing_vfs.json

section "Ошибки: конфиг ссылается на несуществующий скрипт (эмулятор продолжает работу)"
run $PY main.py --config config/missing_script.json

section "Ошибки: неизвестный параметр командной строки"
run $PY main.py --unknown

section "Ошибки: параметр без значения"
run $PY main.py --vfs
