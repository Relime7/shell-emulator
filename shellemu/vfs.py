"""Виртуальная файловая система. Все данные живут только в памяти.

Формат JSON-описания:

    {
      "type": "dir",                  # корень обязан быть каталогом
      "mode": "755",                  # необязательно, восьмеричная строка
      "children": {
        "hello.txt": {"type": "file", "content": "text"},
        "logo.png":  {"type": "file", "encoding": "base64", "content": "iVBORw0KGgo="},
        "sub":       {"type": "dir", "children": {}}
      }
    }
"""
from __future__ import annotations

import base64
import binascii
import json
import re
import time
from dataclasses import dataclass, field

DIR_SIZE = 4096
_MODE_RE = re.compile(r"[0-7]{3,4}")


class VFSError(Exception):
    """Ошибка загрузки или проверки описания VFS."""


@dataclass
class Node:
    kind: str                 # "dir" | "file"
    mode: int                 # права доступа (0o777)
    mtime: float
    data: bytes = b""
    children: dict = field(default_factory=dict)

    @property
    def is_dir(self) -> bool:
        return self.kind == "dir"

    @property
    def size(self) -> int:
        return DIR_SIZE if self.is_dir else len(self.data)


def _parse_mode(value, default: int, where: str) -> int:
    if value is None:
        return default
    if not isinstance(value, str) or not _MODE_RE.fullmatch(value):
        raise VFSError(f"{where}: некорректное поле 'mode' {value!r} "
                       f"(ожидается восьмеричная строка, например \"644\")")
    return int(value, 8) & 0o777


def _build(spec, where: str, now: float) -> Node:
    if not isinstance(spec, dict):
        raise VFSError(f"{where}: узел должен быть JSON-объектом")
    kind = spec.get("type")

    if kind == "dir":
        node = Node("dir", _parse_mode(spec.get("mode"), 0o755, where), now)
        children = spec.get("children", {})
        if not isinstance(children, dict):
            raise VFSError(f"{where}: 'children' должен быть объектом")
        for name, child in children.items():
            if name in ("", ".", "..") or "/" in name:
                raise VFSError(f"{where}: недопустимое имя {name!r}")
            node.children[name] = _build(child, f"{where.rstrip('/')}/{name}", now)
        return node

    if kind == "file":
        mode = _parse_mode(spec.get("mode"), 0o644, where)
        encoding = spec.get("encoding", "text")
        content = spec.get("content", "")
        if not isinstance(content, str):
            raise VFSError(f"{where}: 'content' должен быть строкой")
        if encoding == "text":
            data = content.encode("utf-8")
        elif encoding == "base64":
            try:
                data = base64.b64decode(content, validate=True)
            except (binascii.Error, ValueError):
                raise VFSError(f"{where}: содержимое не является корректным base64")
        else:
            raise VFSError(f"{where}: неизвестная кодировка {encoding!r} "
                           f"(допустимо 'text' или 'base64')")
        return Node("file", mode, now, data=data)

    raise VFSError(f"{where}: неизвестный тип узла {kind!r} (ожидается 'dir' или 'file')")


class VFS:
    def __init__(self, root: Node):
        self.root = root
        self.cwd = "/"

    @classmethod
    def empty(cls) -> "VFS":
        return cls(Node("dir", 0o755, time.time()))

    @classmethod
    def from_file(cls, path: str) -> "VFS":
        try:
            with open(path, "r", encoding="utf-8-sig") as f:
                spec = json.load(f)
        except OSError as e:
            raise VFSError(f"не удалось прочитать VFS '{path}': {e.strerror}")
        except UnicodeDecodeError:
            raise VFSError(f"VFS '{path}' не в кодировке UTF-8")
        except json.JSONDecodeError as e:
            raise VFSError(f"VFS '{path}' - некорректный JSON: {e}")
        root = _build(spec, "/", time.time())
        if not root.is_dir:
            raise VFSError("корень VFS должен быть каталогом")
        return cls(root)

    def stats(self):
        """(каталогов, файлов, байт данных) во всей VFS - для отладочного вывода."""
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

    # ---- работа с путями -------------------------------------------------
    def normalize(self, path: str) -> str:
        """Абсолютный нормализованный путь (учитывает '.', '..', cwd).

        Пустая строка остаётся пустой: lookup('') даёт FileNotFoundError, как в UNIX.
        """
        if path == "":
            return ""
        parts = [] if path.startswith("/") else [p for p in self.cwd.split("/") if p]
        for p in path.split("/"):
            if p in ("", "."):
                continue
            if p == "..":
                if parts:
                    parts.pop()
            else:
                parts.append(p)
        return "/" + "/".join(parts)

    def lookup(self, abs_path: str) -> Node:
        """Найти узел по абсолютному пути.

        Бросает FileNotFoundError / NotADirectoryError.
        """
        if abs_path == "":
            raise FileNotFoundError(abs_path)
        node = self.root
        for part in (p for p in abs_path.split("/") if p):
            if not node.is_dir:
                raise NotADirectoryError(abs_path)
            if part not in node.children:
                raise FileNotFoundError(abs_path)
            node = node.children[part]
        return node
