#!/usr/bin/env bash
# Запуск эмулятора: ./run.sh [--vfs ПУТЬ] [--script ПУТЬ] [--config ПУТЬ]
# Переменная PYTHON задаёт интерпретатор (по умолчанию python3).
exec "${PYTHON:-python3}" "$(dirname "$0")/src/main.py" "$@"
