"""Команды эмулятора. Этап 1: ls и cd - заглушки (имя и аргументы)."""
from __future__ import annotations


class ShellExit(Exception):
    """Сигнал о завершении работы оболочки с заданным кодом."""

    def __init__(self, code: int):
        super().__init__(code)
        self.code = code


class UsageError(Exception):
    """Неверные опции команды; текст сообщения выводится как есть."""


def cmd_ls(shell, args):
    """ls [аргументы...] (заглушка)"""
    print(f"ls (stub): args={args}")
    return 0


def cmd_cd(shell, args):
    """cd [аргументы...] (заглушка)"""
    print(f"cd (stub): args={args}")
    return 0


def cmd_exit(shell, args):
    """exit [КОД]"""
    if len(args) > 1:
        print("exit: too many arguments")
        return 1
    code = shell.status
    if args:
        try:
            code = int(args[0]) & 0xFF
        except ValueError:
            print(f"exit: {args[0]}: numeric argument required")
            code = 2
    raise ShellExit(code)


COMMANDS = {
    "ls": cmd_ls,
    "cd": cmd_cd,
    "exit": cmd_exit,
}
