"""Оболочка: приглашение, REPL и выполнение стартового скрипта."""
from __future__ import annotations

import getpass
import socket
import sys

try:  # история и редактирование строки в интерактивном режиме (Unix)
    import readline  # noqa: F401
except ImportError:
    pass

from .commands import COMMANDS, ShellExit, UsageError
from .parser import ParseError, tokenize
from .vfs import VFS


def _real_user() -> str:
    try:
        return getpass.getuser()
    except Exception:
        return "user"


class Shell:
    def __init__(self, vfs: VFS):
        self.vfs = vfs
        self.user = _real_user()
        self.host = socket.gethostname() or "localhost"
        self.status = 0
        self.oldpwd: str | None = None

    def prompt(self) -> str:
        return f"{self.user}@{self.host}:{self.vfs.cwd}$ "

    def execute(self, line: str) -> None:
        """Выполнить одну строку. Ошибки печатаются, а не бросаются."""
        try:
            tokens = tokenize(line)
        except ParseError as e:
            print(f"emulator: syntax error: {e}")
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
        except UsageError as e:
            print(e)
            self.status = 2

    def run_script(self, path: str) -> int | None:
        """Выполнить стартовый скрипт, показывая и ввод, и вывод.

        Возвращает код выхода, если скрипт вызвал exit, иначе None.
        """
        try:
            with open(path, "r", encoding="utf-8-sig") as f:
                lines = f.read().splitlines()
        except OSError as e:
            print(f"emulator: cannot read script '{path}': {e.strerror}")
            self.status = 2
            return None
        except UnicodeDecodeError:
            print(f"emulator: script '{path}' is not valid UTF-8")
            self.status = 2
            return None

        for raw in lines:
            line = raw.rstrip()
            if not line.strip():
                continue
            if line.lstrip().startswith("#"):
                print(line)               # комментарий показываем как есть
                continue
            print(f"{self.prompt()}{line}")  # имитация ввода пользователя
            try:
                self.execute(line)
            except ShellExit as e:
                return e.code
        return None

    def repl(self) -> int:
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
                print(line)  # при вводе из pipe/файла показываем ввод в диалоге
            try:
                self.execute(line)
            except ShellExit as e:
                return e.code
