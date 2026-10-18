"""Оболочка: приглашение, REPL и выполнение стартового скрипта."""
from __future__ import annotations

import getpass
import importlib
import socket
import sys

from .commands import COMMANDS, ShellExit, UsageError
from .parser import ParseError, tokenize
from .vfs import VFS


def _real_user() -> str:
    """Имя пользователя реальной ОС (запасной вариант - "user")."""
    try:
        return getpass.getuser()
    except (KeyError, OSError):
        return "user"


def _enable_line_editing() -> None:
    """Подключить readline (история, правка строки), если он доступен."""
    try:
        importlib.import_module("readline")
    except ImportError:
        pass


class Shell:
    """Интерпретатор команд, привязанный к виртуальной файловой системе."""

    def __init__(self, vfs: VFS):
        self.vfs = vfs
        self.user = _real_user()
        self.host = socket.gethostname() or "localhost"
        self.status = 0
        self.oldpwd: str | None = None

    def prompt(self) -> str:
        """Приглашение вида имя@хост:каталог$ из данных реальной ОС."""
        return f"{self.user}@{self.host}:{self.vfs.cwd}$ "

    def execute(self, line: str) -> None:
        """Выполнить одну строку. Ошибки печатаются, а не бросаются."""
        try:
            tokens = tokenize(line)
        except ParseError as exc:
            print(f"emulator: syntax error: {exc}")
            self.status = 2
            return
        if not tokens:
            return
        name, args = tokens[0], tokens[1:]
        command = COMMANDS.get(name)
        if command is None:
            print(f"{name}: command not found")
            self.status = 127
            return
        try:
            self.status = command(self, args) or 0
        except UsageError as exc:
            print(exc)
            self.status = 2

    def _read_script(self, path: str):
        """Прочитать строки скрипта; при ошибке вернуть None."""
        try:
            with open(path, "r", encoding="utf-8-sig") as handle:
                return handle.read().splitlines()
        except OSError as exc:
            print(f"emulator: cannot read script '{path}': {exc.strerror}")
        except UnicodeDecodeError:
            print(f"emulator: script '{path}' is not valid UTF-8")
        self.status = 2
        return None

    def run_script(self, path: str) -> int | None:
        """Выполнить стартовый скрипт, показывая и ввод, и вывод.

        Строки-комментарии (#) печатаются как есть, пустые пропускаются,
        остальные выводятся с приглашением, имитируя ввод пользователя.
        Возвращает код выхода, если скрипт вызвал exit, иначе None.
        """
        lines = self._read_script(path)
        if lines is None:
            return None
        for raw in lines:
            line = raw.rstrip()
            if not line.strip():
                continue
            if line.lstrip().startswith("#"):
                print(line)
                continue
            print(f"{self.prompt()}{line}")
            try:
                self.execute(line)
            except ShellExit as exc:
                return exc.code
        return None

    def repl(self) -> int:
        """Интерактивный диалог. Вернуть код выхода.

        Если ввод идёт не с клавиатуры (pipe, файл), введённые строки
        печатаются после приглашения, имитируя диалог.
        """
        _enable_line_editing()
        interactive = sys.stdin.isatty()
        while True:
            try:
                line = input(self.prompt())
            except EOFError:
                print("exit")
                return self.status
            except KeyboardInterrupt:
                print()
                continue
            if not interactive:
                print(line)
            try:
                self.execute(line)
            except ShellExit as exc:
                return exc.code
