"""Модульные тесты: парсер, конфигурация, VFS и оболочка (этапы 1-3)."""
import io
import os
import unittest
from contextlib import redirect_stdout

from shellemu.commands import ShellExit
from shellemu.config import ConfigError, resolve
from shellemu.parser import ParseError, tokenize
from shellemu.shell import Shell
from shellemu.vfs import VFS, VFSError

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), os.pardir)


def repo_path(*parts):
    """Путь к файлу внутри репозитория."""
    return os.path.join(ROOT, *parts)


def run_line(shell, line):
    """Выполнить строку в оболочке и вернуть напечатанный текст."""
    buf = io.StringIO()
    with redirect_stdout(buf):
        shell.execute(line)
    return buf.getvalue()


class ParserTests(unittest.TestCase):
    """Проверки токенизатора командной строки."""

    def test_plain_and_quotes(self):
        """Кавычки и экранирование не разрывают аргументы."""
        tokens = tokenize('ls  -l "a b" \'c d\' e\\ f')
        self.assertEqual(tokens, ["ls", "-l", "a b", "c d", "e f"])

    def test_empty_args_and_adjacent_quotes(self):
        """Пустые аргументы сохраняются, соседние кавычки склеиваются."""
        tokens = tokenize('x "" \'\' "a""b"')
        self.assertEqual(tokens, ["x", "", "", "ab"])

    def test_comments(self):
        """Комментарий начинается только с начала слова."""
        self.assertEqual(tokenize("ls # note"), ["ls"])
        self.assertEqual(tokenize("# only comment"), [])
        self.assertEqual(tokenize("a#b"), ["a#b"])
        self.assertEqual(
            tokenize('echo "# not comment"'), ["echo", "# not comment"])

    def test_errors(self):
        """Незакрытые кавычки и хвостовой обратный слеш - ошибки."""
        for bad in ('ls "x', "ls 'x", "ls x\\"):
            with self.assertRaises(ParseError):
                tokenize(bad)


class ConfigTests(unittest.TestCase):
    """Проверки чтения параметров запуска."""

    def test_cli_overrides_file(self):
        """Параметр командной строки перекрывает конфигурационный файл."""
        base = repo_path("config", "default.json")
        settings = resolve("cli.json", None, base)
        self.assertEqual(settings.vfs_path, "cli.json")
        self.assertEqual(settings.sources["vfs"], "командная строка")
        self.assertEqual(
            settings.sources["script"], "конфигурационный файл")

    def test_missing_config(self):
        """Отсутствующий конфиг даёт ConfigError."""
        with self.assertRaises(ConfigError):
            resolve(None, None, "no_such_config.json")


class VFSTests(unittest.TestCase):
    """Проверки виртуальной файловой системы."""

    def test_bad_vfs(self):
        """Все некорректные описания VFS отвергаются."""
        broken = repo_path("vfs", "broken")
        for name in os.listdir(broken):
            with self.assertRaises(VFSError, msg=name):
                VFS.from_file(os.path.join(broken, name))

    def test_normalize(self):
        """Нормализация путей учитывает '.', '..' и текущий каталог."""
        vfs = VFS.empty()
        vfs.cwd = "/a/b"
        self.assertEqual(vfs.normalize("../c/./d"), "/a/c/d")
        self.assertEqual(vfs.normalize("/../.."), "/")

    def test_load_deep(self):
        """Описание с вложенностью загружается, base64 декодируется."""
        vfs = VFS.from_file(repo_path("vfs", "deep.json"))
        node = vfs.lookup("/home/user/projects/emulator/data.bin")
        self.assertEqual(node.data, bytes(range(10)))


class ShellTests(unittest.TestCase):
    """Проверки оболочки: заглушки, ошибки, выход."""

    @staticmethod
    def make_shell():
        """Оболочка с пустой VFS."""
        return Shell(VFS.empty())

    def test_stubs_print_name_and_args(self):
        """Заглушки печатают имя команды и список аргументов."""
        shell = self.make_shell()
        self.assertEqual(
            run_line(shell, 'ls -l "a b"'),
            "ls (stub): args=['-l', 'a b']\n")
        self.assertEqual(run_line(shell, "cd x"), "cd (stub): args=['x']\n")

    def test_unknown_command(self):
        """Неизвестная команда даёт код 127."""
        shell = self.make_shell()
        self.assertIn("command not found", run_line(shell, "nope"))
        self.assertEqual(shell.status, 127)

    def test_syntax_error_is_reported(self):
        """Синтаксическая ошибка печатается, а не бросается."""
        shell = self.make_shell()
        self.assertIn("syntax error", run_line(shell, 'ls "x'))
        self.assertEqual(shell.status, 2)

    def test_exit_code(self):
        """exit N завершает оболочку с кодом N."""
        shell = self.make_shell()
        with self.assertRaises(ShellExit) as caught:
            shell.execute("exit 7")
        self.assertEqual(caught.exception.code, 7)


if __name__ == "__main__":
    unittest.main()
