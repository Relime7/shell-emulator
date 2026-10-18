import io
import os
import sys
import unittest
from contextlib import redirect_stdout

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from shellemu.commands import ShellExit  # noqa: E402
from shellemu.config import ConfigError, resolve  # noqa: E402
from shellemu.parser import ParseError, tokenize  # noqa: E402
from shellemu.shell import Shell  # noqa: E402
from shellemu.vfs import VFS, VFSError  # noqa: E402


class ParserTests(unittest.TestCase):
    def test_plain_and_quotes(self):
        self.assertEqual(tokenize('ls  -l "a b" \'c d\' e\\ f'), ["ls", "-l", "a b", "c d", "e f"])

    def test_empty_args_and_adjacent_quotes(self):
        self.assertEqual(tokenize('x "" \'\' "a""b"'), ["x", "", "", "ab"])

    def test_comments(self):
        self.assertEqual(tokenize("ls # note"), ["ls"])
        self.assertEqual(tokenize("# only comment"), [])
        self.assertEqual(tokenize("a#b"), ["a#b"])
        self.assertEqual(tokenize('echo "# not comment"'), ["echo", "# not comment"])

    def test_errors(self):
        for bad in ('ls "x', "ls 'x", "ls x\\"):
            with self.assertRaises(ParseError):
                tokenize(bad)


class ConfigTests(unittest.TestCase):
    def test_cli_overrides_file(self):
        base = os.path.join(os.path.dirname(__file__), "..", "config", "default.json")
        s = resolve("cli.json", None, base)
        self.assertEqual(s.vfs_path, "cli.json")
        self.assertEqual(s.sources["vfs"], "командная строка")
        self.assertEqual(s.sources["script"], "конфигурационный файл")

    def test_missing_config(self):
        with self.assertRaises(ConfigError):
            resolve(None, None, "no_such_config.json")


class VFSTests(unittest.TestCase):
    def test_bad_vfs(self):
        broken = os.path.join(os.path.dirname(__file__), "..", "vfs", "broken")
        for name in os.listdir(broken):
            with self.assertRaises(VFSError, msg=name):
                VFS.from_file(os.path.join(broken, name))

    def test_normalize(self):
        v = VFS.empty()
        v.cwd = "/a/b"
        self.assertEqual(v.normalize("../c/./d"), "/a/c/d")
        self.assertEqual(v.normalize("/../.."), "/")


class ShellTests(unittest.TestCase):
    def setUp(self):
        self.sh = Shell(VFS.empty())

    def out(self, line):
        buf = io.StringIO()
        with redirect_stdout(buf):
            self.sh.execute(line)
        return buf.getvalue()

    def test_stubs_print_name_and_args(self):
        self.assertEqual(self.out('ls -l "a b"'), "ls (stub): args=['-l', 'a b']\n")
        self.assertEqual(self.out("cd x"), "cd (stub): args=['x']\n")

    def test_unknown_command(self):
        self.assertIn("command not found", self.out("nope"))
        self.assertEqual(self.sh.status, 127)

    def test_syntax_error_is_reported(self):
        self.assertIn("syntax error", self.out('ls "x'))
        self.assertEqual(self.sh.status, 2)

    def test_exit_code(self):
        with self.assertRaises(ShellExit) as cm:
            self.sh.execute("exit 7")
        self.assertEqual(cm.exception.code, 7)


if __name__ == "__main__":
    unittest.main()
