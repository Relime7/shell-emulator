#!/usr/bin/env bash
# Этап 1: REPL, приглашение, кавычки, ошибки, exit. Ввод подаётся через stdin,
# эмулятор сам показывает введённые строки, имитируя диалог.
source "$(dirname "$0")/common.sh"

section "Этап 1: диалог (кавычки, ошибки разбора, неизвестная команда)"
run_stdin "$(cat scripts/os/input_stage1_a.txt)\n" $PY main.py

section "Этап 1: пустые строки, комментарии, exit с кодом"
run_stdin "$(cat scripts/os/input_stage1_b.txt)\n" $PY main.py

section "Этап 1: завершение по Ctrl+D (конец ввода)"
run_stdin "$(cat scripts/os/input_stage1_c.txt)" $PY main.py

section "Этап 1: exit с некорректным аргументом"
run_stdin "$(cat scripts/os/input_stage1_d.txt)\n" $PY main.py
