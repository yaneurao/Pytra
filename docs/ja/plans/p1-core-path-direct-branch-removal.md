# P1: `core.py` の `Path` 直分岐撤去

最終更新: 2026-03-01

関連 TODO:
- `docs/ja/todo/index.md` の `ID: P1-CORE-PATH-SOT-01`

背景:
- `src/pytra/compiler/east_parts/core.py` には `fn_name == "Path"` など、標準ライブラリ個別名に依存する直分岐が残っている。
- `Path` は `pytra/std/pathlib.py` 側が仕様正本であり、compiler 側に同等知識を重複保持すると追従漏れの原因になる。
- `P0-STDLIB-SOT` で `perf_counter` の是正を進めているが、`Path` 系は未撤去のため追加計画として管理する。

目的:
- `core.py` から `Path` 文字列直書きの戻り値推論・BuiltinCall 判定分岐を撤去する。
- `Path` の解決は stdlib 参照層（シグネチャ/属性情報）と import 解決情報へ一本化する。

対象:
- `src/pytra/compiler/east_parts/core.py`
- `src/pytra/compiler/stdlib/signature_registry.py`（必要時）
- `test/unit/test_east_core.py`（回帰）

非対象:
- `Path` API 仕様の変更
- backend 側 emitter の大規模改修

受け入れ基準:
- `core.py` から `fn_name == "Path"` のような `Path` 直分岐が撤去される。
- `from pathlib import Path` / `from pytra.std.pathlib import Path` の双方で `Path(...)` の戻り値推論と BuiltinCall lower が維持される。
- 既存回帰（`test_east_core.py`、`check_py2cpp_transpile.py`）が非退行で通る。

確認コマンド（予定）:
- `python3 tools/check_todo_priority.py`
- `python3 -m unittest discover -s test/unit -p 'test_east_core.py' -v`
- `python3 tools/check_py2cpp_transpile.py`

## 分解

- [ ] [ID: P1-CORE-PATH-SOT-01] `core.py` の `Path` 直分岐を撤去し、stdlib 参照層 + import 解決情報へ一本化する。
- [x] [ID: P1-CORE-PATH-SOT-01-S1-01] `core.py` の `Path` 依存分岐（戻り値推論 / BuiltinCall lower / 属性推論）を棚卸しし、置換先 API を固定する。
- [ ] [ID: P1-CORE-PATH-SOT-01-S2-01] `Path` 判定を名前直書きから resolver 経由へ置換し、`core.py` から `fn_name == "Path"` を削除する。
- [ ] [ID: P1-CORE-PATH-SOT-01-S2-02] `Path` の constructor / method / attribute の戻り値推論を stdlib 参照層で補完し、`core.py` 側重複知識を増やさない。
- [ ] [ID: P1-CORE-PATH-SOT-01-S3-01] `test_east_core.py` に再混入防止回帰を追加し、`Path` 直書き再導入を検知可能にする。
- [ ] [ID: P1-CORE-PATH-SOT-01-S3-02] `check_py2cpp_transpile.py` を実行し、非退行を確認する。

## S1-01 棚卸し結果（`core.py` の `Path` 直依存）

### 1. `Path` 直分岐の位置

- `src/pytra/compiler/east_parts/core.py:2437`
  - `Call(Name)` の戻り値推論で `elif fn_name == "Path": call_ret = "Path"`。
- `src/pytra/compiler/east_parts/core.py:2489`
  - `Call(Attribute)` の戻り値推論で `if owner_t == "Path": ...`（`read_text/name/stem/exists/mkdir/write_text`）。
- `src/pytra/compiler/east_parts/core.py:2561`
  - BuiltinCall lower で `elif fn_name == "Path": runtime_call = "Path"`。
- `src/pytra/compiler/east_parts/core.py:2918`
  - `BinOp "/"` の型推論で `lt == "Path"` を直比較して `Path` を返す。

### 2. 既存の stdlib 参照 API（再利用可能）

- `lookup_stdlib_function_return_type(fn_name)`
- `lookup_stdlib_function_runtime_call(fn_name)`
- `lookup_stdlib_method_runtime_call(owner_t, attr)`
- `lookup_stdlib_attribute_type(owner_t, attr)`
- 備考: `lookup_stdlib_method_return_type(owner_t, method)` は `signature_registry.py` に存在するが `core.py` 未利用。

### 3. 置換方針（S2 実装用）

- constructor 判定:
  - `fn_name == "Path"` 直比較を撤去し、import 解決情報（`meta.import_symbols`）経由で `pathlib.Path` シンボルかを判定する resolver を追加する。
- 戻り値推論:
  - `Path` メソッド戻り値は `lookup_stdlib_method_return_type("Path", method)` を一次情報にし、`core.py` 固有辞書を持たない。
- BuiltinCall lower:
  - `Path` constructor runtime_call は resolver 判定を通したときのみ `runtime_call="Path"` を付与する。
- `BinOp "/"`:
  - `Path` 固有演算は「左辺が stdlib `Path` と解決済み」判定へ置換し、`lt == "Path"` 直比較を排除する。

決定ログ:
- 2026-03-01: ユーザー指示により、`Path` 直分岐を `core.py` から撤去する方針を `P1` で管理開始した。
- 2026-03-01: `core.py` 内の `Path` 直依存4箇所（戻り値推論2、BuiltinCall1、演算型推論1）と再利用可能な stdlib API を棚卸しし、S2 置換方針を確定した（`S1-01`）。
