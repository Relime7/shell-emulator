#!/usr/bin/env python3
"""Точка входа эмулятора командной строки."""
from shellemu.shell import Shell

if __name__ == "__main__":
    raise SystemExit(Shell().repl())
