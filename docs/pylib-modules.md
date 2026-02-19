# `src/pylib/` モジュール一覧

このページは、`src/pylib/` のサポート済みモジュールと公開 API 一覧です。  
`_` で始まる名前は内部実装扱いで、サポート対象外です。
ここに未記載の関数/クラスを呼び出した場合、変換時エラーまたは変換先コンパイルエラーになる可能性があります。

## 1. Python標準モジュール代替（互換層）

- `pylib.std.pathlib`（`pathlib` 代替）
  - class: `Path`
  - `Path` の主なメンバー: `parent`, `parents`, `name`, `suffix`, `stem`, `resolve()`, `exists()`, `mkdir(parents=False, exist_ok=False)`, `read_text()`, `write_text()`, `glob()`, `cwd()`
- `pylib.std.json`（`json` 代替）
  - 関数: `loads(text)`, `dumps(obj, ensure_ascii=True, indent=None, separators=None)`
- `pylib.std.sys`（`sys` 代替）
  - 変数: `argv`, `path`, `stderr`, `stdout`
  - 関数: `exit(code=0)`, `set_argv(values)`, `set_path(values)`, `write_stderr(text)`, `write_stdout(text)`
- `pylib.std.typing`（`typing` 代替）
  - 型エイリアス: `Any`, `List`, `Set`, `Dict`, `Tuple`, `Iterable`, `Sequence`, `Mapping`, `Optional`, `Union`, `Callable`, `TypeAlias`
  - 関数: `TypeVar(name)`
- `pylib.std.os`（`os` 代替・最小実装）
  - 変数: `path`
  - `path` の主なメンバー: `join`, `dirname`, `basename`, `splitext`, `abspath`, `exists`
  - 関数: `getcwd()`, `mkdir(path)`, `makedirs(path, exist_ok=False)`
- `pylib.std.glob`（`glob` 代替・最小実装）
  - 関数: `glob(pattern)`
- `pylib.std.argparse`（`argparse` 代替・最小実装）
  - class: `ArgumentParser`, `Namespace`
  - `ArgumentParser` の主な機能: `add_argument(...)`, `parse_args(...)`
- `pylib.std.re`（`re` 代替・最小実装）
  - 定数: `S`
  - class: `Match`
  - 関数: `match(pattern, text, flags=0)`, `sub(pattern, repl, text, flags=0)`
- `pylib.std.dataclasses`（`dataclasses` 代替・最小実装）
  - デコレータ: `dataclass`
- `pylib.std.enum`（`enum` 代替・最小実装）
  - class: `Enum`, `IntEnum`, `IntFlag`
  - 制約: クラス本体のメンバーは `NAME = expr` 形式を使用してください。

## 2. Pytra独自モジュール

- `pylib.tra.assertions`
  - 関数: `py_assert_true(cond, label="")`, `py_assert_eq(actual, expected, label="")`, `py_assert_all(results, label="")`, `py_assert_stdout(expected_lines, fn)`
- `pylib.tra.png`
  - 関数: `write_rgb_png(path, width, height, pixels)`
- `pylib.tra.gif`
  - 関数: `grayscale_palette()`, `save_gif(path, width, height, frames, palette, delay_cs=4, loop=0)`
- `pylib.tra.east`
  - クラス/定数: `EastBuildError`, `BorrowKind`, `INT_TYPES`, `FLOAT_TYPES`
  - 関数: `convert_source_to_east(...)`, `convert_source_to_east_self_hosted(...)`, `convert_source_to_east_with_backend(...)`, `convert_path(...)`, `render_east_human_cpp(...)`, `main()`
- `pylib.tra.east_parts.east_io`
  - 関数: `extract_module_leading_trivia(source)`, `load_east_from_path(input_path, parser_backend="self_hosted")`
