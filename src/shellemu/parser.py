r"""Разбор командной строки на токены.

Поддерживается (как в bash):
  * разделение по пробелам и табуляциям;
  * 'одинарные кавычки'   - всё внутри буквально;
  * "двойные кавычки"     - внутри работают \" \\ \$ \`;
  * экранирование \x вне кавычек;
  * пустые аргументы ("" и '');
  * комментарии: '#' в начале слова до конца строки.
"""
from __future__ import annotations

WHITESPACE = " \t\r\n"
DOUBLE_QUOTE_ESCAPES = '"\\$`'


class ParseError(Exception):
    """Синтаксическая ошибка во введённой строке."""


def _read_single_quoted(line: str, pos: int) -> tuple[str, int]:
    """Прочитать '...' с открывающей кавычки: (текст, новая позиция)."""
    end = line.find("'", pos + 1)
    if end == -1:
        raise ParseError("unterminated single quote")
    return line[pos + 1:end], end + 1


def _read_double_quoted(line: str, pos: int) -> tuple[str, int]:
    """Прочитать "..." с открывающей кавычки: (текст, новая позиция)."""
    chars: list[str] = []
    index = pos + 1
    while index < len(line):
        char = line[index]
        if char == '"':
            return "".join(chars), index + 1
        escaped = (char == "\\" and index + 1 < len(line)
                   and line[index + 1] in DOUBLE_QUOTE_ESCAPES)
        if escaped:
            chars.append(line[index + 1])
            index += 2
        else:
            chars.append(char)
            index += 1
    raise ParseError("unterminated double quote")


def _read_escaped(line: str, pos: int) -> tuple[str, int]:
    """Прочитать символ после обратной косой черты."""
    if pos + 1 >= len(line):
        raise ParseError("unexpected end of line after backslash")
    return line[pos + 1], pos + 2


def _read_piece(line: str, pos: int) -> tuple[str, int]:
    """Прочитать часть слова: цитату, экранированный или обычный символ."""
    char = line[pos]
    if char == "'":
        return _read_single_quoted(line, pos)
    if char == '"':
        return _read_double_quoted(line, pos)
    if char == "\\":
        return _read_escaped(line, pos)
    return char, pos + 1


def tokenize(line: str) -> list[str]:
    """Разбить строку на аргументы с учётом кавычек и комментариев."""
    tokens: list[str] = []
    buf: list[str] = []
    in_word = False
    pos = 0
    while pos < len(line):
        char = line[pos]
        if char in WHITESPACE:
            if in_word:
                tokens.append("".join(buf))
                buf, in_word = [], False
            pos += 1
        elif char == "#" and not in_word:
            break
        else:
            text, pos = _read_piece(line, pos)
            buf.append(text)
            in_word = True
    if in_word:
        tokens.append("".join(buf))
    return tokens
