# `src/pylib/` モジュール一覧

このページは、`src/pylib/` のサポート済みモジュールと公開 API 一覧です。  
`_` で始まる名前は内部実装扱いで、サポート対象外です。

## 1. Python標準モジュール代替（互換層）

- `pylib.pathlib`（`pathlib` 代替）
  - class: `Path`
  - `Path` の主なメンバー: `parent`, `parents`, `name`, `suffix`, `stem`, `resolve()`, `exists()`, `mkdir(parents=False, exist_ok=False)`, `read_text()`, `write_text()`, `glob()`, `cwd()`
- `pylib.json`（`json` 代替）
  - 関数: `loads(text)`, `dumps(obj, ensure_ascii=True, indent=None, separators=None)`
- `pylib.sys`（`sys` 代替）
  - 変数: `argv`, `path`, `stderr`, `stdout`
  - 関数: `exit(code=0)`, `set_argv(values)`, `set_path(values)`, `write_stderr(text)`, `write_stdout(text)`
- `pylib.typing`（`typing` 代替）
  - 型エイリアス: `Any`, `List`, `Set`, `Dict`, `Tuple`, `Iterable`, `Sequence`, `Mapping`, `Optional`, `Union`, `Callable`, `TypeAlias`
  - 関数: `TypeVar(name)`
- `pylib.argparse`（`argparse` 代替・最小実装）
  - class: `ArgumentParser`, `Namespace`
  - `ArgumentParser` の主な機能: `add_argument(...)`, `parse_args(...)`
- `pylib.re`（`re` 代替・最小実装）
  - 定数: `S`
  - class: `Match`
  - 関数: `match(pattern, text, flags=0)`, `sub(pattern, repl, text, flags=0)`

## 2. Pytra独自モジュール

- `pylib.assertions`
  - 関数: `py_assert_true(cond, label="")`, `py_assert_eq(actual, expected, label="")`, `py_assert_all(results, label="")`, `py_assert_stdout(expected_lines, fn)`
- `pylib.png`
  - 関数: `write_rgb_png(path, width, height, pixels)`
- `pylib.gif`
  - 関数: `grayscale_palette()`, `save_gif(path, width, height, frames, palette, delay_cs=4, loop=0)`
- `pylib.east`
  - クラス/定数: `EastBuildError`, `BorrowKind`, `INT_TYPES`, `FLOAT_TYPES`
  - 関数: `convert_source_to_east(...)`, `convert_source_to_east_self_hosted(...)`, `convert_source_to_east_with_backend(...)`, `convert_path(...)`, `render_east_human_cpp(...)`, `main()`
- `pylib.east_io`
  - 関数: `extract_module_leading_trivia(source)`, `load_east_from_path(input_path, parser_backend="self_hosted")`
