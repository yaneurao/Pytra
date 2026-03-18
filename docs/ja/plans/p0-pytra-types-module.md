# P0: pytra.types モジュール追加（Pylance 互換スカラー型定義）

最終更新: 2026-03-18

関連 TODO:
- `docs/ja/todo/index.md` の `ID: P0-PYTRA-TYPES-MODULE-01`

## 背景

`int64`, `uint8` 等の Pytra 固有スカラー型名は Python 標準に存在しないため、
VS Code の Pylance が未定義警告を出す。

## 修正方針

1. `src/pytra/types.py` に `int8 = int`, `uint8 = int`, `int64 = int`, `float64 = float` 等を定義
2. ソースファイルで `from pytra.types import int64, uint8` 等を記述して Pylance 警告を解消
3. 変換器（パーサー）は `from pytra.types import ...` を無視する（型名は既にパーサーが認識済み）

## 対象

- `src/pytra/types.py` — 新規作成
- `src/toolchain/ir/core_module_parser.py` — `pytra.types` import の無視
- `src/pytra/std/argparse.py` — `from pytra.types import int64` 追加（検証用）

## 非対象

- 既存の全ソースファイルへの一括適用（必要に応じて段階的に追加）

## 受け入れ基準

- `src/pytra/types.py` が存在し、全スカラー型が定義されている。
- `from pytra.types import int64` を含むファイルが transpile できる（import が無視される）。
- 既存の fixture / sample pass。

## 決定ログ

- 2026-03-18: ユーザー指摘。`int64` が Pylance で未定義警告になる。`pytra.types` モジュールで Python 実行時は `int` / `float` にエイリアスし、変換器では import を無視する方針に決定。
- 2026-03-18: 実装完了。`src/pytra/types.py` 作成。`core_module_parser.py` で `pytra.types` import を無視。`argparse.py` に `from pytra.types import int64` を追加して検証。241 test pass。
