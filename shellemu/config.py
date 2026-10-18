"""Параметры запуска: командная строка + JSON-конфиг (CLI приоритетнее)."""
from __future__ import annotations

import json
from dataclasses import dataclass, field

SRC_CLI = "командная строка"
SRC_FILE = "конфигурационный файл"
SRC_NONE = "не задан"


class ConfigError(Exception):
    pass


@dataclass
class Settings:
    config_path: str | None = None
    vfs_path: str | None = None
    script_path: str | None = None
    sources: dict = field(default_factory=dict)


def load_config_file(path: str) -> dict:
    """Читает JSON-конфиг: {"vfs_path": "...", "script_path": "..."}."""
    try:
        with open(path, "r", encoding="utf-8-sig") as f:
            data = json.load(f)
    except OSError as e:
        raise ConfigError(f"не удалось прочитать конфигурационный файл '{path}': {e.strerror}")
    except UnicodeDecodeError:
        raise ConfigError(f"конфигурационный файл '{path}' не в кодировке UTF-8")
    except json.JSONDecodeError as e:
        raise ConfigError(f"конфигурационный файл '{path}' - некорректный JSON: {e}")
    if not isinstance(data, dict):
        raise ConfigError(f"конфигурационный файл '{path}': ожидается JSON-объект")
    for key in ("vfs_path", "script_path"):
        if data.get(key) is not None and not isinstance(data[key], str):
            raise ConfigError(f"конфигурационный файл '{path}': поле '{key}' должно быть строкой")
    return data


def resolve(cli_vfs, cli_script, cli_config) -> Settings:
    file_values = load_config_file(cli_config) if cli_config is not None else {}

    def pick(key, cli_value):
        if cli_value is not None:
            return cli_value, SRC_CLI
        if file_values.get(key) is not None:
            return file_values[key], SRC_FILE
        return None, SRC_NONE

    s = Settings(config_path=cli_config)
    s.vfs_path, vfs_src = pick("vfs_path", cli_vfs)
    s.script_path, script_src = pick("script_path", cli_script)
    s.sources = {
        "config": SRC_CLI if cli_config is not None else SRC_NONE,
        "vfs": vfs_src,
        "script": script_src,
    }
    return s
