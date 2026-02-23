# P0 Iterable/Iterator 契約反映（最優先）

ID: `TG-P0-ITER`

## 関連 TODO

- `docs-jp/todo.md` の `ID: P0-ITER-01`（`P0-ITER-01-S1` 〜 `P0-ITER-01-S4`）

## 背景

- `materials/refs/spec-iterable.md` に、`for ... in ...` の動作を Python の `iter/next` 契約へ寄せる改良案を整理した。
- 現状は `object/Any` 境界で反復契約が不安定で、ユーザー定義 `__iter__/__next__` と non-iterable 失敗契約が十分に固定されていない。
- この領域は `spec-boxing` の境界契約とも強く連動するため、優先して仕様固定と実装計画化が必要。

## 目的

- `docs-jp/spec/spec-iterable.md` を実装時の正本仕様として扱う。
- `EAST` の `iter_mode` / `iterable_trait` と runtime の `py_iter_or_raise` / `py_next_or_stop` を一貫した契約で導入する。
- `list` 系の静的 fastpath と `object/Any` の動的 protocol を両立する。

## 非対象

- `async for` / `__aiter__` / `__anext__` 対応。
- 例外メッセージ文言の CPython 完全一致。
- 性能最適化のみを目的とした先行変更。

## サブタスク実行順（todo 同期）

1. `P0-ITER-01-S1`: `EAST` trait（`iterable_trait` / `iter_mode`）で必要なメタデータを確定し、影響ノードを整理する。
2. `P0-ITER-01-S2`: parser/lower から `EAST` trait を供給できるようにし、既存 `For` への互換移行を固定する。
3. `P0-ITER-01-S3`: C++ runtime に `py_iter_or_raise` / `py_next_or_stop` / `py_dyn_range` を実装し、non-iterable fail-fast 契約を固定する。
4. `P0-ITER-01-S4`: `py2cpp` の `static_fastpath` / `runtime_protocol` 分岐と回帰テストを整備する。

## `P0-ITER-01-S1` 棚卸し結果

- 必須メタデータ（`For` ノード）:
  - `iter_mode`: `static_fastpath | runtime_protocol`
  - `iter_source_type`: 反復元の解決型（空なら `unknown`）
  - `iter_element_type`: 反復要素型（空なら `unknown`）
- 必須メタデータ（`For.iter` 式ノード）:
  - `iterable_trait`: `yes | no | unknown`
  - `iter_protocol`: `static_range | runtime_protocol`
  - `iter_element_type`: `For.iter_element_type` と同じ規約で保持
- 生成側（producer）:
  - `src/pytra/compiler/east_parts/core.py` の `for` 解析で `iter_mode` / `iter_source_type` / `iter_element_type` を `For` に付与し、`iterable_trait` / `iter_protocol` を `iter` 式へ注入する。
- 消費側（consumer）:
  - `src/py2cpp.py` の `emit_for_each` が `_resolve_for_iter_mode` で `iter_mode` を解決し、`_emit_for_each_runtime` で `py_dyn_range(...)` 経路を生成する。
  - `iter_mode` が欠落した旧 EAST は `_resolve_for_iter_mode` で `static_fastpath` へフォールバックし互換維持する。
- 影響ノード:
  - 直接影響: `For`（新規メタデータ利用）
  - 隣接影響: `ForRange`（`for range(...)` lower の分岐点だが `iter_mode` 非依存）
- 既存回帰テスト:
  - `test/unit/test_east_core.py::test_for_iter_mode_and_iterable_traits_are_annotated`
  - `test/unit/test_py2cpp_codegen_issues.py::test_for_object_uses_runtime_protocol_py_dyn_range`
  - `test/unit/test_py2cpp_codegen_issues.py::test_for_list_keeps_static_fastpath`

## 受け入れ基準

- `object/Any` の `for` が `__iter__` / `__next__` を経由して動作する。
- non-iterable の `for` が `TypeError` 相当で失敗する。
- `list` fastpath では `py_dyn_range` が生成されない。
- 同一入力で mode ごとの dispatch 方式が決定的に切り替わる。

## 決定ログ

- 2026-02-23: `materials/refs/spec-iterable.md` を `docs-jp/spec/spec-iterable.md` へコピーし、`P0-ITER-01` を TODO 最優先に追加。
- 2026-02-23: Phase 1 として C++ runtime に `PyObj::py_iter_or_raise` / `PyObj::py_next_or_stop` と `py_iter_or_raise(...)` / `py_next_or_stop(...)` / `py_dyn_range(...)` を導入し、`PyListObj` / `PyDictObj` / `PyStrObj` は iterator object を返す実装へ更新した。non-iterable は `TypeError` 相当（`runtime_error`）で fail-fast とする。
- 2026-02-23: `py2cpp` の `For` 生成は `iter_mode`（`static_fastpath` / `runtime_protocol`）で分岐する。`runtime_protocol` は `for (object ... : py_dyn_range(iterable))` を生成し、tuple unpack は `py_at(...)` で展開する。
- 2026-02-23: selfhost 安定性のため、`iter_mode` 未付与の既存 EAST は `unknown` を既定 `static_fastpath` として扱う（互換優先）。`object/Any` は parser 側で明示 `runtime_protocol` を付与して切り替える。
- 2026-02-23: C++ runtime の object iterable 経路で `set` を扱えるようにした。`PySetObj`（`PYTRA_TID_SET`）と `make_object(const set<T>&)` を追加し、`py_dyn_range(make_object(set<...>))` が反復可能であること、`py_isinstance(make_object(set<...>), PYTRA_TID_SET)` が成立することを `test/unit/test_cpp_runtime_iterable.py` / `test/unit/test_cpp_runtime_type_id.py` で固定した。
- 2026-02-23: docs-jp/todo.md の P0-ITER-01 を -S1 〜 -S4 へ分割したため、本 plan 側にも同粒度の実行順を追記した。
- 2026-02-23: `P0-ITER-01-S1` を完了。`EAST` の必須 trait（`iter_mode` / `iter_source_type` / `iter_element_type` / `iterable_trait` / `iter_protocol`）と影響ノード（`For` / `ForRange`）を棚卸しし、producer（`core.py`）と consumer（`py2cpp.py`）の責務境界を固定した。回帰として `python3 test/unit/test_east_core.py`、`python3 test/unit/test_py2cpp_codegen_issues.py` を実行して既存契約が維持されることを確認した。
- 2026-02-23: `P0-ITER-01-S2` を完了。`core.py` の `For` 生成で trait 供給済みであることを維持しつつ、`test/unit/test_py2cpp_codegen_issues.py::test_for_without_iter_mode_keeps_legacy_static_fastpath` を追加して「`iter_mode` 欠落の旧 EAST は static 側へフォールバックする」互換契約を固定した。`python3 test/unit/test_py2cpp_codegen_issues.py`（42件成功）で回帰なしを確認した。
- 2026-02-23: `P0-ITER-01-S3` を完了。C++ runtime の `py_iter_or_raise` / `py_next_or_stop` / `py_dyn_range` 実装と non-iterable fail-fast 契約を `python3 test/unit/test_cpp_runtime_iterable.py`（1件成功、compile+run）で再確認した。
- 2026-02-23: `P0-ITER-01-S4` を完了。`py2cpp` の `emit_for_each` / `_resolve_for_iter_mode` / `_emit_for_each_runtime` が `static_fastpath` / `runtime_protocol` を切替える実装であることを固定し、`python3 test/unit/test_py2cpp_codegen_issues.py`（42件成功）と `python3 tools/check_py2cpp_transpile.py`（`checked=131 ok=131 fail=0 skipped=6`）で回帰なしを確認した。
