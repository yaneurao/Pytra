# `src/pytra/` モジュール一覧

<a href="../../en/spec/spec-pylib-modules.md">
  <img alt="Read in English" src="https://img.shields.io/badge/docs-English-2563EB?style=flat-square">
</a>


このページは、`src/pytra/` のサポート済みモジュールと公開 API 一覧です。  
`_` で始まる名前は内部実装扱いで、サポート対象外です。
ここに未記載の関数/クラスを呼び出した場合、変換時エラーまたは変換先コンパイルエラーになる可能性があります。

## 0. `pylib` 配置方針（目的）

- `src/pytra/std/`:
  - 目的: Python 標準モジュール（`json`, `pathlib`, `sys`, `typing`, `os`, `glob`, `argparse`, `re`, `dataclasses`, `enum` など）の**代替実装**を提供するための領域です。
  - 方針: トランスパイル対象コードで Python 標準モジュールを直接 `import` せず、`pytra.std.*` を使えるようにします。
  - ルール: Python 標準モジュール代替は原則として `src/pytra/std/` に配置します。
- `src/pytra/utils/`:
  - 目的: Pytra 固有の機能（例: EAST 変換、画像出力ヘルパー、アサーション補助）を提供するための領域です。
  - 方針: Python 標準モジュールの代替ではない、トランスパイラ/ランタイム都合の機能をここへ集約します。
  - ルール: Pytra 独自モジュールは `src/pytra/utils/` に配置します。

## 1. Python標準モジュール代替（互換層）

- `pytra.std.pathlib`（`pathlib` 代替）
  - class: `Path`
  - `Path` の主なメンバー: `parent`, `parents`, `name`, `suffix`, `stem`, `resolve()`, `exists()`, `mkdir(parents=False, exist_ok=False)`, `read_text()`, `write_text()`, `glob()`, `cwd()`
- `pytra.std.math`（`math` 代替）
  - 定数: `pi`, `e`
  - 関数: `sqrt`, `sin`, `cos`, `tan`, `exp`, `log`, `log10`, `fabs`, `floor`, `ceil`, `pow`
- `pytra.std.time`（`time` 代替・最小実装）
  - 関数: `perf_counter()`
- `pytra.std.timeit`（`timeit` 代替・最小実装）
  - 関数: `default_timer()`
- `pytra.std.json`（`json` 代替）
  - 関数: `loads(text)`, `dumps(obj, ensure_ascii=True, indent=None, separators=None)`
- `pytra.std.sys`（`sys` 代替）
  - 変数: `argv`, `path`, `stderr`, `stdout`
  - 関数: `exit(code=0)`, `set_argv(values)`, `set_path(values)`, `write_stderr(text)`, `write_stdout(text)`
- `pytra.std.typing`（`typing` 代替）
  - 型エイリアス: `Any`, `List`, `Set`, `Dict`, `Tuple`, `Iterable`, `Sequence`, `Mapping`, `Optional`, `Union`, `Callable`, `TypeAlias`
  - 関数: `TypeVar(name)`
  - 現状: `TypeVar(name)` は最小 shim（`name` をそのまま返す）であり、template 型パラメータ機能は提供しません。
- `pytra.std.os`（`os` 代替・最小実装）
  - 変数: `path`
  - `path` の主なメンバー: `join`, `dirname`, `basename`, `splitext`, `abspath`, `exists`
  - 関数: `getcwd()`, `mkdir(path)`, `makedirs(path, exist_ok=False)`
- `pytra.std.glob`（`glob` 代替・最小実装）
  - 関数: `glob(pattern)`
- `pytra.std.argparse`（`argparse` 代替・最小実装）
  - class: `ArgumentParser`, `Namespace`
  - `ArgumentParser` の主な機能: `add_argument(...)`, `parse_args(...)`
- `pytra.std.re`（`re` 代替・最小実装）
  - 定数: `S`
  - class: `Match`
  - 関数: `match(pattern, text, flags=0)`, `sub(pattern, repl, text, flags=0)`
- `pytra.std.dataclasses`（`dataclasses` 代替・最小実装）
  - デコレータ: `dataclass`
- `pytra.std.enum`（`enum` 代替・最小実装）
  - class: `Enum`, `IntEnum`, `IntFlag`
  - 制約: クラス本体のメンバーは `NAME = expr` 形式を使用してください。
- `pytra.std.random`（`random` 代替・最小実装）
  - 関数: `seed(value)`, `random()`, `randint(a, b)`, `choices(population, weights, k=1)`, `gauss(mu=0.0, sigma=1.0)`, `shuffle(xs)`
- `pytra.std.traceback`（`traceback` 代替・最小実装）
  - 関数: `format_exc()`

## 2. Pytra独自モジュール

- `pytra.utils.assertions`
  - 関数: `py_assert_true(cond, label="")`, `py_assert_eq(actual, expected, label="")`, `py_assert_all(results, label="")`, `py_assert_stdout(expected_lines, fn)`
- `pytra.utils.png`
  - 関数: `write_rgb_png(path, width, height, pixels)`
- `pytra.utils.gif`
  - 関数: `grayscale_palette()`, `save_gif(path, width, height, frames, palette, delay_cs=4, loop=0)`
- `pytra.utils.browser`
  - 変数/クラス: `document`, `window`, `DOMEvent`, `Element`, `CanvasRenderingContext`
- `pytra.utils.browser.widgets.dialog`
  - クラス: `Dialog`, `EntryDialog`, `InfoDialog`
- `pytra.compiler.east`
  - クラス/定数: `EastBuildError`, `BorrowKind`, `INT_TYPES`, `FLOAT_TYPES`
  - 関数: `convert_source_to_east(...)`, `convert_source_to_east_self_hosted(...)`, `convert_source_to_east_with_backend(...)`, `convert_path(...)`, `render_east_human_cpp(...)`, `main()`
- `pytra.compiler.east_parts.east_io`
  - 関数: `extract_module_leading_trivia(source)`, `load_east_from_path(input_path, parser_backend="self_hosted")`
