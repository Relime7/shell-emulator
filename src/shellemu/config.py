"""Параметры запуска: командная строка и JSON-конфигурация.

Значения из командной строки приоритетнее значений из файла.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field

SRC_CLI = "командная строка"
SRC_FILE = "конфигурационный файл"
SRC_NONE = "не задан"
PATH_KEYS = ("vfs_path", "script_path")


class ConfigError(Exception):
    """Ошибка чтения или проверки конфигурационного файла."""


@dataclass
class Settings:
    """Итоговые параметры запуска и источник каждого значения."""

    config_path: str | None = None
    vfs_path: str | None = None
    script_path: str | None = None
    sources: dict = field(default_factory=dict)


def _read_json(path: str):
    """Прочитать JSON-файл конфигурации."""
    try:
        with open(path, "r", encoding="utf-8-sig") as handle:
            return json.load(handle)
    except OSError as exc:
        raise ConfigError(
            f"не удалось прочитать конфигурационный файл '{path}': "
            f"{exc.strerror}") from exc
    except UnicodeDecodeError as exc:
        raise ConfigError(
            f"конфигурационный файл '{path}' не в кодировке UTF-8") from exc
    except json.JSONDecodeError as exc:
        raise ConfigError(
            f"конфигурационный файл '{path}' - некорректный JSON: {exc}"
        ) from exc


def load_config_file(path: str) -> dict:
    """Прочитать и проверить конфиг {"vfs_path": "...", "script_path": ...}."""
    data = _read_json(path)
    if not isinstance(data, dict):
        raise ConfigError(
            f"конфигурационный файл '{path}': ожидается JSON-объект")
    for key in PATH_KEYS:
        if data.get(key) is not None and not isinstance(data[key], str):
            raise ConfigError(
                f"конфигурационный файл '{path}': "
                f"поле '{key}' должно быть строкой")
    return data


def _pick(key: str, cli_value, file_values: dict):
    """Выбрать значение параметра и источник: CLI, затем файл."""
    if cli_value is not None:
        return cli_value, SRC_CLI
    if file_values.get(key) is not None:
        return file_values[key], SRC_FILE
    return None, SRC_NONE


def resolve(cli_vfs, cli_script, cli_config) -> Settings:
    """Объединить параметры командной строки и конфигурационного файла."""
    file_values = {}
    if cli_config is not None:
        file_values = load_config_file(cli_config)
    settings = Settings(config_path=cli_config)
    settings.vfs_path, vfs_src = _pick("vfs_path", cli_vfs, file_values)
    settings.script_path, script_src = _pick(
        "script_path", cli_script, file_values)
    settings.sources = {
        "config": SRC_CLI if cli_config is not None else SRC_NONE,
        "vfs": vfs_src,
        "script": script_src,
    }
    return settings
