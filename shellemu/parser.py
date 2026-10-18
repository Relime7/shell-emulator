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


class ParseError(Exception):
    """Синтаксическая ошибка во введённой строке."""


def tokenize(line: str) -> list[str]:
    tokens: list[str] = []
    buf: list[str] = []
    in_word = False
    i, n = 0, len(line)

    while i < n:
        c = line[i]
        if c in " \t\r\n":
            if in_word:
                tokens.append("".join(buf))
                buf, in_word = [], False
            i += 1
        elif c == "#" and not in_word:
            break  # комментарий до конца строки
        elif c == "'":
            end = line.find("'", i + 1)
            if end == -1:
                raise ParseError("unterminated single quote")
            buf.append(line[i + 1:end])
            in_word = True
            i = end + 1
        elif c == '"':
            i += 1
            closed = False
            while i < n:
                ch = line[i]
                if ch == '"':
                    closed = True
                    i += 1
                    break
                if ch == "\\" and i + 1 < n and line[i + 1] in '"\\$`':
                    buf.append(line[i + 1])
                    i += 2
                    continue
                buf.append(ch)
                i += 1
            if not closed:
                raise ParseError("unterminated double quote")
            in_word = True
        elif c == "\\":
            if i + 1 >= n:
                raise ParseError("unexpected end of line after backslash")
            buf.append(line[i + 1])
            in_word = True
            i += 2
        else:
            buf.append(c)
            in_word = True
            i += 1

    if in_word:
        tokens.append("".join(buf))
    return tokens
