# `src/pytra/built_in` 運用ルール

このディレクトリは、target 非依存の built-in 意味論を pure Python で管理する正本レイヤです。

## 配置ルール

- 正本は `src/pytra/built_in/*.py`。
- target 固有コード（C++ の `#include`、JS/TS のランタイム依存 API 直呼びなど）はここに書かない。
- GC/ABI など低レベルのブート処理は target 側（例: `src/runtime/cpp/native/core/`）に残す。

## 命名ルール

- モジュール名は `snake_case.py`。
- 1 モジュール 1 責務（例: `type_id.py`, `isinstance_impl.py`）。
- `_impl` 接尾辞は使わない（`_impl` は target 側手書きファイル予約）。

## 生成対象ルール

- `src/pytra/built_in/<name>.py` は
  `src/runtime/cpp/generated/built_in/<name>.{h,cpp}` へ生成し、C++ compiler はその generated header を直接使う。
- 他言語も同一方針で `src/runtime/<lang>/built_in/` へ展開する。
- 生成層を厚くし、手書き層は最小ブート処理だけに限定する。

## テスト運用

- 仕様追加時は unit test か fixture を同時追加し、既存 runtime との観測結果差分を検証する。

## 現在の実装

- `type_id.py`: `py_tid_register_class_type` / `py_tid_is_subtype` / `py_tid_issubclass` / `py_tid_runtime_type_id` / `py_tid_isinstance` の pure Python 実装。
- `contains.py`: object 経路の `py_contains` helper（`dict/list/set/str`）の pure Python 実装。
- `sequence.py`: `py_range` / `py_repeat(str, int)` の pure Python 実装。
- `iter_ops.py`: object 経路の `py_reversed` / `py_enumerate` の pure Python 実装。
- `string_ops.py`: `py_strip` / `py_find` / `py_replace` 系の文字列 helper の pure Python 実装。
- `predicates.py`: `py_any` / `py_all` の pure Python 実装。
