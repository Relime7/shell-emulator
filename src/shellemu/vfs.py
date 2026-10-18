"""Виртуальная файловая система. Все данные живут только в памяти.

Формат JSON-описания::

    {
      "type": "dir",
      "mode": "755",
      "children": {
        "hello.txt": {"type": "file", "content": "text"},
        "logo.png":  {"type": "file", "encoding": "base64",
                      "content": "iVBORw0KGgo="},
        "sub":       {"type": "dir", "children": {}}
      }
    }

Корень обязан быть каталогом. Поле ``mode`` необязательно (восьмеричная
строка), по умолчанию 755 для каталогов и 644 для файлов.
"""
from __future__ import annotations

import base64
import binascii
import json
import re
import time
from dataclasses import dataclass, field

DIR_SIZE = 4096
MODE_RE = re.compile(r"[0-7]{3,4}")


class VFSError(Exception):
    """Ошибка загрузки или проверки описания VFS."""


@dataclass
class Node:
    """Узел файловой системы.

    kind - "dir" или "file"; mode - права доступа (0o777); mtime - время
    изменения; data - содержимое файла; children - потомки каталога.
    """

    kind: str
    mode: int
    mtime: float
    data: bytes = b""
    children: dict = field(default_factory=dict)

    @property
    def is_dir(self) -> bool:
        """Является ли узел каталогом."""
        return self.kind == "dir"

    @property
    def size(self) -> int:
        """Размер в байтах (для каталога условные 4096)."""
        return DIR_SIZE if self.is_dir else len(self.data)


def _parse_mode(value, default: int, where: str) -> int:
    """Преобразовать поле mode (восьмеричная строка) в число."""
    if value is None:
        return default
    if not isinstance(value, str) or not MODE_RE.fullmatch(value):
        raise VFSError(
            f"{where}: некорректное поле 'mode' {value!r} "
            f"(ожидается восьмеричная строка, например \"644\")")
    return int(value, 8) & 0o777


def _decode_content(content, encoding, where: str) -> bytes:
    """Получить байты содержимого файла по его кодировке."""
    if not isinstance(content, str):
        raise VFSError(f"{where}: 'content' должен быть строкой")
    if encoding == "text":
        return content.encode("utf-8")
    if encoding == "base64":
        try:
            return base64.b64decode(content, validate=True)
        except (binascii.Error, ValueError) as exc:
            raise VFSError(
                f"{where}: содержимое не является корректным base64"
            ) from exc
    raise VFSError(
        f"{where}: неизвестная кодировка {encoding!r} "
        f"(допустимо 'text' или 'base64')")


def _build_file(spec: dict, where: str, now: float) -> Node:
    """Создать файловый узел по описанию."""
    mode = _parse_mode(spec.get("mode"), 0o644, where)
    data = _decode_content(
        spec.get("content", ""), spec.get("encoding", "text"), where)
    return Node("file", mode, now, data=data)


def _build_dir(spec: dict, where: str, now: float) -> Node:
    """Создать каталог и всех его потомков по описанию."""
    node = Node("dir", _parse_mode(spec.get("mode"), 0o755, where), now)
    children = spec.get("children", {})
    if not isinstance(children, dict):
        raise VFSError(f"{where}: 'children' должен быть объектом")
    for name, child in children.items():
        if name in ("", ".", "..") or "/" in name:
            raise VFSError(f"{where}: недопустимое имя {name!r}")
        child_path = f"{where.rstrip('/')}/{name}"
        node.children[name] = _build(child, child_path, now)
    return node


def _build(spec, where: str, now: float) -> Node:
    """Рекурсивно построить узел по JSON-описанию."""
    if not isinstance(spec, dict):
        raise VFSError(f"{where}: узел должен быть JSON-объектом")
    kind = spec.get("type")
    if kind == "dir":
        return _build_dir(spec, where, now)
    if kind == "file":
        return _build_file(spec, where, now)
    raise VFSError(
        f"{where}: неизвестный тип узла {kind!r} "
        f"(ожидается 'dir' или 'file')")


def _read_json(path: str):
    """Прочитать JSON-файл с описанием VFS."""
    try:
        with open(path, "r", encoding="utf-8-sig") as handle:
            return json.load(handle)
    except OSError as exc:
        raise VFSError(
            f"не удалось прочитать VFS '{path}': {exc.strerror}") from exc
    except UnicodeDecodeError as exc:
        raise VFSError(f"VFS '{path}' не в кодировке UTF-8") from exc
    except json.JSONDecodeError as exc:
        raise VFSError(f"VFS '{path}' - некорректный JSON: {exc}") from exc


class VFS:
    """Виртуальная файловая система с текущим каталогом."""

    def __init__(self, root: Node):
        self.root = root
        self.cwd = "/"

    @classmethod
    def empty(cls) -> "VFS":
        """Пустая файловая система (только корневой каталог)."""
        return cls(Node("dir", 0o755, time.time()))

    @classmethod
    def from_file(cls, path: str) -> "VFS":
        """Загрузить VFS из JSON-файла."""
        root = _build(_read_json(path), "/", time.time())
        if not root.is_dir:
            raise VFSError("корень VFS должен быть каталогом")
        return cls(root)

    def stats(self):
        """Вернуть (каталогов, файлов, байт данных) - для отладки."""
        dirs = files = size = 0
        stack = [self.root]
        while stack:
            node = stack.pop()
            if node.is_dir:
                dirs += 1
                stack.extend(node.children.values())
            else:
                files += 1
                size += len(node.data)
        return dirs, files, size

    def normalize(self, path: str) -> str:
        """Абсолютный нормализованный путь (учитывает '.', '..', cwd).

        Пустая строка остаётся пустой: lookup('') даёт FileNotFoundError,
        как в UNIX.
        """
        if path == "":
            return ""
        start = "" if path.startswith("/") else self.cwd
        parts = [part for part in start.split("/") if part]
        for part in path.split("/"):
            if part in ("", "."):
                continue
            if part == "..":
                if parts:
                    parts.pop()
            else:
                parts.append(part)
        return "/" + "/".join(parts)

    def lookup(self, abs_path: str) -> Node:
        """Найти узел по абсолютному пути.

        Бросает FileNotFoundError или NotADirectoryError.
        """
        if abs_path == "":
            raise FileNotFoundError(abs_path)
        node = self.root
        for part in (item for item in abs_path.split("/") if item):
            if not node.is_dir:
                raise NotADirectoryError(abs_path)
            if part not in node.children:
                raise FileNotFoundError(abs_path)
            node = node.children[part]
        return node
