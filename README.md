# Эмулятор командной строки UNIX-подобной ОС

Практическое задание №1, **вариант №3**: эмулятор языка оболочки ОС, максимально
похожий на работу в командной строке UNIX. Реализация на Python 3.8+, используется
только стандартная библиотека.

В репозитории выполнены **этапы 1-3**: REPL, конфигурация и виртуальная файловая система.

## Запуск

```
python main.py [--vfs ПУТЬ] [--script ПУТЬ] [--config ПУТЬ]
```

В Windows вместо `python` может понадобиться `py -3` (см. раздел «Windows»).

| Параметр   | Описание |
|------------|----------|
| `--vfs`    | путь к JSON-файлу с описанием виртуальной файловой системы; без него используется пустая VFS |
| `--script` | путь к стартовому скрипту; команды выполняются с показом ввода и вывода, после чего начинается обычный диалог |
| `--config` | путь к JSON-конфигурации с ключами `vfs_path` и `script_path` |

Значения из командной строки приоритетнее значений из конфигурационного файла.
При запуске эмулятор печатает все заданные параметры вместе с источником каждого (`[debug] ...`).

## Структура репозитория

```
main.py                    точка входа
shellemu/
  parser.py                собственный токенизатор строки (кавычки, экранирование, комментарии)
  shell.py                 приглашение, REPL, выполнение стартового скрипта
  commands.py              команды: заглушки ls и cd, команда exit
  vfs.py                   виртуальная файловая система в памяти, загрузка из JSON
  config.py                параметры запуска: командная строка + JSON-конфиг
  cli.py                   разбор аргументов, отладочный вывод, запуск
vfs/                       примеры VFS: minimal, files, deep; vfs/broken/ - некорректные описания
config/                    примеры конфигурационных файлов (в том числе с ошибками)
scripts/*.emu              стартовые скрипты эмулятора (комментарии начинаются с #)
scripts/os/*.sh, *.bat     скрипты реальной ОС (Linux/macOS и Windows), вызывающие эмулятор
tests/test_emulator.py     модульные тесты
```

## Этап 1. REPL

- Консольное приложение. Приглашение строится из данных реальной ОС:
  `имя_пользователя@имя_хоста:текущий_каталог$` (`getpass.getuser()`, `socket.gethostname()`).
- Парсер (`shellemu/parser.py`) написан вручную и ведёт себя как в bash:

| Конструкция | Пример | Результат |
|-------------|--------|-----------|
| пробелы и табуляции разделяют аргументы | `ls  -l   a` | `ls`, `-l`, `a` |
| двойные кавычки | `ls "my docs"` | аргумент `my docs` |
| одинарные кавычки (всё буквально) | `ls 'a "b" c'` | аргумент `a "b" c` |
| экранирование | `ls my\ docs` | аргумент `my docs` |
| пустой аргумент | `ls "" x` | `ls`, пустая строка, `x` |
| склейка частей | `ls "my"" docs"` | аргумент `my docs` |
| комментарий | `ls # note` | `ls` |

- Незакрытая кавычка и завершающий `\` дают сообщение `emulator: syntax error: ...`, а не падение.
- Неизвестная команда: `имя: command not found`.
- `exit [код]` завершает работу; Ctrl+D (конец ввода) тоже. Код возврата последней команды
  становится кодом выхода.
- `ls` и `cd` на этом этапе - заглушки: они печатают своё имя и аргументы, например
  `ls (stub): args=['-l', 'a b']`. Настоящая логика команд - предмет следующих этапов.

Диалог (ввод из `scripts/os/input_stage1_a.txt`; когда ввод не с клавиатуры, эмулятор сам
печатает введённые строки, имитируя диалог):

```
[debug] Параметры запуска эмулятора:
[debug]   config = <не задан>  (источник: не задан)
[debug]   vfs    = <не задан>  (источник: не задан)
[debug]   script = <не задан>  (источник: не задан)
[debug] VFS не задана - используется пустая файловая система
user@host:/$ ls
ls (stub): args=[]
user@host:/$ cd
cd (stub): args=[]
user@host:/$ cd "dir with spaces"
cd (stub): args=['dir with spaces']
user@host:/$ ls -l "a b" 'c d' e\ f
ls (stub): args=['-l', 'a b', 'c d', 'e f']
user@host:/$ ls "" x
ls (stub): args=['', 'x']
user@host:/$ unknown arg "x y"
unknown: command not found
user@host:/$ ls "unterminated
emulator: syntax error: unterminated double quote
user@host:/$ ls 'unterminated
emulator: syntax error: unterminated single quote
user@host:/$ exit
```

Демонстрация целиком: `bash scripts/os/stage1_repl.sh` или `scripts\os\stage1_repl.bat`.

## Этап 2. Конфигурация

Конфигурационный файл (`config/default.json`):

```json
{ "vfs_path": "vfs/files.json", "script_path": "scripts/hello.emu" }
```

Приоритет: **командная строка > конфигурационный файл > значение по умолчанию**.
Параметры можно задавать частично: например, `--config config/only_vfs.json --script ...`.
Стартовый скрипт поддерживает комментарии `#` (на отдельной строке и в конце строки);
при выполнении на экране видны и ввод, и вывод. Если скрипт не завершился командой `exit`,
эмулятор продолжает интерактивный диалог.

Только конфигурационный файл:

```
$ python main.py --config config/default.json
[debug] Параметры запуска эмулятора:
[debug]   config = 'config/default.json'  (источник: командная строка)
[debug]   vfs    = 'vfs/files.json'  (источник: конфигурационный файл)
[debug]   script = 'scripts/hello.emu'  (источник: конфигурационный файл)
[debug] VFS загружена: каталогов 2, файлов 5, байт данных 81
# Простой стартовый скрипт: комментарии, пустые строки и команды
user@host:/$ ls            # комментарий в конце строки
ls (stub): args=[]
user@host:/$ ls -l readme.txt "my docs"
ls (stub): args=['-l', 'readme.txt', 'my docs']
user@host:/$ cd "my docs"
cd (stub): args=['my docs']
user@host:/$ cd ..
cd (stub): args=['..']
user@host:/$ exit
```

Параметр командной строки перекрывает файл (`--vfs vfs/minimal.json` вместо `vfs/files.json`):

```
$ python main.py --config config/default.json --vfs vfs/minimal.json
[debug] Параметры запуска эмулятора:
[debug]   config = 'config/default.json'  (источник: командная строка)
[debug]   vfs    = 'vfs/minimal.json'  (источник: командная строка)
[debug]   script = 'scripts/hello.emu'  (источник: конфигурационный файл)
[debug] VFS загружена: каталогов 1, файлов 0, байт данных 0
# Простой стартовый скрипт: комментарии, пустые строки и команды
user@host:/$ ls            # комментарий в конце строки
ls (stub): args=[]
user@host:/$ ls -l readme.txt "my docs"
ls (stub): args=['-l', 'readme.txt', 'my docs']
user@host:/$ cd "my docs"
cd (stub): args=['my docs']
user@host:/$ cd ..
cd (stub): args=['..']
user@host:/$ exit
```

Ошибки конфигурации (код возврата 2):

```
$ python main.py --config config/broken.json
emulator: ошибка конфигурации: конфигурационный файл 'config/broken.json' - некорректный JSON: Expecting value: line 2 column 1 (char 48)
$ python main.py --config config/no_such.json
emulator: ошибка конфигурации: не удалось прочитать конфигурационный файл 'config/no_such.json': No such file or directory
$ python main.py --config config/bad_types.json
emulator: ошибка конфигурации: конфигурационный файл 'config/bad_types.json': поле 'vfs_path' должно быть строкой
```

Скрипты, проверяющие все параметры командной строки: `scripts/os/stage2_params.sh`
и `scripts\os\stage2_params.bat`.

## Этап 3. Виртуальная файловая система

Все операции выполняются в памяти: описание VFS читается из JSON один раз, на диск
ничего не распаковывается и не записывается. Двоичные данные хранятся в base64.

```json
{
  "type": "dir",
  "children": {
    "readme.txt": { "type": "file", "content": "text" },
    "logo.png":   { "type": "file", "encoding": "base64", "content": "iVBORw0KGgo=" },
    "secret":     { "type": "file", "content": "x", "mode": "600" },
    "sub":        { "type": "dir", "mode": "755", "children": {} }
  }
}
```

Поля: `type` (`dir`/`file`), `children` (для каталога), `content`, `encoding`
(`text` по умолчанию или `base64`), `mode` (необязательная восьмеричная строка).
Минимальная VFS: `{ "type": "dir", "children": {} }`.

Три варианта VFS из репозитория (минимальная, несколько файлов, 6 уровней вложенности):

```
$ python main.py --vfs vfs/minimal.json
[debug]   config = <не задан>  (источник: не задан)
[debug]   vfs    = 'vfs/minimal.json'  (источник: командная строка)
[debug]   script = <не задан>  (источник: не задан)
[debug] VFS загружена: каталогов 1, файлов 0, байт данных 0
user@host:/$ exit

$ python main.py --vfs vfs/files.json
[debug]   config = <не задан>  (источник: не задан)
[debug]   vfs    = 'vfs/files.json'  (источник: командная строка)
[debug]   script = <не задан>  (источник: не задан)
[debug] VFS загружена: каталогов 2, файлов 5, байт данных 81
user@host:/$ exit

$ python main.py --vfs vfs/deep.json
[debug]   config = <не задан>  (источник: не задан)
[debug]   vfs    = 'vfs/deep.json'  (источник: командная строка)
[debug]   script = <не задан>  (источник: не задан)
[debug] VFS загружена: каталогов 12, файлов 13, байт данных 162
user@host:/$ exit
```

Ошибки загрузки описания VFS (код возврата 2):

```
$ python main.py --vfs vfs/broken/bad_base64.json
emulator: ошибка VFS: /a: содержимое не является корректным base64
$ python main.py --vfs vfs/broken/bad_type.json
emulator: ошибка VFS: /a: неизвестный тип узла 'symlink' (ожидается 'dir' или 'file')
$ python main.py --vfs vfs/broken/bad_mode.json
emulator: ошибка VFS: /: некорректное поле 'mode' '999' (ожидается восьмеричная строка, например "644")
$ python main.py --vfs vfs/broken/invalid_json.json
emulator: ошибка VFS: VFS 'vfs/broken/invalid_json.json' - некорректный JSON: Expecting value: line 2 column 1 (char 30)
$ python main.py --vfs vfs/broken/root_is_file.json
emulator: ошибка VFS: корень VFS должен быть каталогом
```

Команды `ls` и `cd` на этом этапе остаются заглушками, поэтому загруженная VFS видна по
отладочной строке со статистикой (каталоги, файлы, байты данных после декодирования base64);
работа команд с VFS - следующий этап.

Скрипты: `scripts/os/stage3_vfs.sh`, `scripts\os\stage3_vfs.bat` (все варианты VFS и
некорректные описания), `scripts/full_test.emu` (стартовый скрипт для проверки всех команд).

## Тестирование

```
python -m unittest discover -s tests
```
```
----------------------------------------------------------------------
Ran 12 tests in 0.001s

OK
```

Скрипты реальной ОС вызывают эмулятор с разными параметрами:

| Linux / macOS | Windows | Что проверяет |
|---------------|---------|---------------|
| `bash scripts/os/stage1_repl.sh` | `scripts\os\stage1_repl.bat` | диалог, кавычки, ошибки, `exit` |
| `bash scripts/os/stage2_params.sh` | `scripts\os\stage2_params.bat` | `--vfs`, `--script`, `--config`, приоритеты, ошибки |
| `bash scripts/os/stage3_vfs.sh` | `scripts\os\stage3_vfs.bat` | три варианта VFS, некорректные VFS, полный тест |

Стартовый скрипт эмулятора можно запускать и напрямую:

```
python main.py --vfs vfs/deep.json --script scripts/full_test.emu
```

Начало его вывода:

```
[debug] VFS загружена: каталогов 12, файлов 13, байт данных 162
# ###################### ТЕСТ ВСЕХ КОМАНД (этапы 1-3), VFS: vfs/deep.json ######################
# === Этап 1: парсер, кавычки, ошибки (VFS: vfs/deep.json) ===
user@host:/$ ls
ls (stub): args=[]
user@host:/$ ls "my docs"
ls (stub): args=['my docs']
user@host:/$ ls 'my docs'
ls (stub): args=['my docs']
user@host:/$ ls my\ docs
ls (stub): args=['my docs']
user@host:/$ ls "my docs" readme.txt
ls (stub): args=['my docs', 'readme.txt']
user@host:/$ ls "my"" docs"
ls (stub): args=['my docs']
user@host:/$ ls "" x
```

## Windows

В Windows команда `python3` часто оказывается заглушкой Microsoft Store. Используйте
`python` или `py -3`; для `.bat`-скриптов интерпретатор можно задать так: `set PY=py -3`.
Скрипты `.bat` сами включают кодировку UTF-8 (`chcp 65001`). Запускать эмулятор нужно из
папки репозитория, потому что пути к `vfs/` и `scripts/` указываются относительно неё.
Конец ввода в Windows - Ctrl+Z, затем Enter.

## История коммитов

Каждый этап сохранён отдельным коммитом в стиле Conventional Commits:

```
feat(repl): add REPL with OS-based prompt, quote-aware parser and ls/cd stubs
feat(config): add CLI/JSON configuration with debug output and startup scripts
feat(vfs): add in-memory virtual file system loaded from JSON
test: add unit tests for parser, config, VFS and shell
docs: add README with usage and demonstrations
```
