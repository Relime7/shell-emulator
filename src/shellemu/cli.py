"""Командная строка эмулятора: параметры, отладочный вывод, запуск."""
from __future__ import annotations

import argparse
import sys

from .config import ConfigError, resolve
from .shell import Shell
from .vfs import VFS, VFSError


def build_arg_parser() -> argparse.ArgumentParser:
    """Создать разборщик параметров командной строки."""
    parser = argparse.ArgumentParser(
        prog="main.py",
        description="Эмулятор командной строки UNIX-подобной ОС.")
    parser.add_argument(
        "--vfs", metavar="ПУТЬ", help="путь к JSON-файлу с описанием VFS")
    parser.add_argument(
        "--script", metavar="ПУТЬ", help="путь к стартовому скрипту")
    parser.add_argument(
        "--config", metavar="ПУТЬ", help="путь к JSON-конфигурации")
    return parser


def print_debug(settings) -> None:
    """Напечатать все параметры запуска и источник каждого."""
    rows = (
        ("config", settings.config_path, settings.sources["config"]),
        ("vfs", settings.vfs_path, settings.sources["vfs"]),
        ("script", settings.script_path, settings.sources["script"]),
    )
    print("[debug] Параметры запуска эмулятора:")
    for name, value, source in rows:
        shown = repr(value) if value is not None else "<не задан>"
        print(f"[debug]   {name:<7}= {shown}  (источник: {source})")


def load_vfs(path):
    """Загрузить VFS (или создать пустую) и напечатать отладочную строку."""
    if not path:
        print("[debug] VFS не задана - используется пустая файловая система")
        return VFS.empty()
    vfs = VFS.from_file(path)
    dirs, files, size = vfs.stats()
    print(f"[debug] VFS загружена: каталогов {dirs}, файлов {files}, "
          f"байт данных {size}")
    return vfs


def main(argv=None) -> int:
    """Запустить эмулятор; вернуть код завершения процесса."""
    args = build_arg_parser().parse_args(argv)
    try:
        settings = resolve(args.vfs, args.script, args.config)
    except ConfigError as exc:
        print(f"emulator: ошибка конфигурации: {exc}", file=sys.stderr)
        return 2

    print_debug(settings)
    try:
        vfs = load_vfs(settings.vfs_path)
    except VFSError as exc:
        print(f"emulator: ошибка VFS: {exc}", file=sys.stderr)
        return 2

    shell = Shell(vfs)
    if settings.script_path:
        code = shell.run_script(settings.script_path)
        if code is not None:
            return code
    return shell.repl()
