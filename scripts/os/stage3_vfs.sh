#!/usr/bin/env bash
# Этап 3: разные варианты VFS (минимальный, несколько файлов, 3+ уровня) и ошибки загрузки.
source "$(dirname "$0")/common.sh"

section "Минимальная VFS (пустой корень)"
run $PY main.py --vfs vfs/minimal.json --script scripts/vfs_probe.emu

section "VFS с несколькими файлами (текст, base64-бинарник, скрытый файл, пробелы в именах)"
run $PY main.py --vfs vfs/files.json --script scripts/vfs_probe.emu

section "VFS с вложенностью 6 уровней"
run $PY main.py --vfs vfs/deep.json --script scripts/vfs_probe.emu

section "Ошибки: корень VFS - файл"
run $PY main.py --vfs vfs/broken/root_is_file.json
section "Ошибки: неизвестный тип узла"
run $PY main.py --vfs vfs/broken/bad_type.json
section "Ошибки: некорректный base64"
run $PY main.py --vfs vfs/broken/bad_base64.json
section "Ошибки: некорректный mode"
run $PY main.py --vfs vfs/broken/bad_mode.json
section "Ошибки: невалидный JSON"
run $PY main.py --vfs vfs/broken/invalid_json.json
section "Ошибки: файл VFS не существует"
run $PY main.py --vfs vfs/nope.json

section "Полный тест всех команд всех этапов (VFS: deep.json)"
run $PY main.py --vfs vfs/deep.json --script scripts/full_test.emu
