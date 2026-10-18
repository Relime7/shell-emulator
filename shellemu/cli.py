"""Командная строка эмулятора: разбор параметров, отладочный вывод, запуск."""
from __future__ import annotations

import argparse
import sys

from .config import ConfigError, resolve
from .shell import Shell
from .vfs import VFS, VFSError


def build_arg_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="main.py",
        description="Эмулятор командной строки UNIX-подобной ОС.")
    p.add_argument("--vfs", metavar="ПУТЬ", help="путь к JSON-файлу с описанием VFS")
    p.add_argument("--script", metavar="ПУТЬ", help="путь к стартовому скрипту")
    p.add_argument("--config", metavar="ПУТЬ", help="путь к JSON-конфигурации")
    return p


def print_debug(settings) -> None:
    rows = (
        ("config", settings.config_path, settings.sources["config"]),
        ("vfs", settings.vfs_path, settings.sources["vfs"]),
        ("script", settings.script_path, settings.sources["script"]),
    )
    print("[debug] Параметры запуска эмулятора:")
    for name, value, source in rows:
        shown = repr(value) if value is not None else "<не задан>"
        print(f"[debug]   {name:<7}= {shown}  (источник: {source})")


def main(argv=None) -> int:
    args = build_arg_parser().parse_args(argv)

    try:
        settings = resolve(args.vfs, args.script, args.config)
    except ConfigError as e:
        print(f"emulator: ошибка конфигурации: {e}", file=sys.stderr)
        return 2

    print_debug(settings)

    try:
        vfs = VFS.from_file(settings.vfs_path) if settings.vfs_path else VFS.empty()
    except VFSError as e:
        print(f"emulator: ошибка VFS: {e}", file=sys.stderr)
        return 2

    if settings.vfs_path:
        dirs, files, size = vfs.stats()
        print(f"[debug] VFS загружена: каталогов {dirs}, файлов {files}, байт данных {size}")
    else:
        print("[debug] VFS не задана - используется пустая файловая система")

    shell = Shell(vfs)
    if settings.script_path:
        code = shell.run_script(settings.script_path)
        if code is not None:
            return code
    return shell.repl()
