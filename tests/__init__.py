"""Пакет тестов: добавляет каталог src в путь импорта модулей."""
import os
import sys

SRC_DIR = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), os.pardir, "src")
sys.path.insert(0, os.path.abspath(SRC_DIR))
